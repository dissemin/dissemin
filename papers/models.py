# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from solo.models import SingletonModel
from celery.execute import send_task

from papers.utils import nstr, iunaccent, create_paper_plain_fingerprint
from papers.name import match_names, name_similarity, unify_name_lists
from papers.utils import remove_diacritics, sanitize_html, validate_orcid, affiliation_is_greater
from papers.orcid import *

from statistics.models import AccessStatistics
from publishers.models import Publisher, Journal, OA_STATUS_CHOICES, OA_STATUS_PREFERENCE, DummyPublisher
from upload.models import UploadedPDF
from dissemin.settings import PROFILE_REFRESH_ON_LOGIN

import hashlib, re
from datetime import datetime, timedelta
from urllib import urlencode, quote # for the Google Scholar and CORE link


PDF_STATUS_CHOICES = [('OK', _('Available')),
                      ('NOK', _('Unavailable'))]

VISIBILITY_CHOICES = [('VISIBLE', _('Visible')),
                      ('CANDIDATE', _('Candidate')),
                      ('NOT_RELEVANT', _('Not relevant')),
                      ('DELETED', _('Deleted')),
                      ]

COMBINED_STATUS_CHOICES = [
   ('oa', _('Open access')),
   ('ok', _('Preprint available')),
   ('couldbe', _('Unavailable but compatible')),
   ('unk', _('Unknown status')),
   ('closed', _('Preprints forbidden'))
]

PAPER_TYPE_CHOICES = [
   ('journal-article', _('Journal article')),
   ('proceedings-article', _('Proceedings article')),
   ('book-chapter', _('Book chapter')),
   ('book', _('Book')),
   ('journal-issue', _('Journal issue')),
   ('proceedings', _('Proceedings')),
   ('reference-entry', _('Entry')),
   ('poster', _('Poster')),
   ('report', _('Report')),
   ('thesis', _('Thesis')),
   ('dataset', _('Dataset')),
   ('preprint', _('Preprint')),
   ('other', _('Other document')),
   ]

UPLOAD_TYPE_CHOICES = [
   ('preprint', _('Preprint')),
   ('postprint', _('Postprint')),
   ('pdfversion', _("Published version")),
   ]

PAPER_TYPE_PREFERENCE = [x for (x,y) in PAPER_TYPE_CHOICES]

HARVESTER_TASK_CHOICES = [
   ('init', _('Preparing profile')),
   ('orcid', _('Fetching publications from ORCID')),
   ('crossref', _('Fetching publications from CrossRef')),
   ('base', _('Fetching publications from BASE')),
   ('core', _('Fetching publications from CORE')),
   ('oai', _('Fetching publications from OAI-PMH')),
   ('clustering', _('Clustering publications')),
   ('stats', _('Updating statistics')),
   ]

class NameVariant(models.Model):
    """
    A NameVariant is a binary relation between names and researchers. When present, it indicates
    that a given name is a possible name for the researcher. The confidence that papers with that
    name are authored by the given researcher is indicated by a confidence score.
    """

    #: The :py:class:`Name` that is part of the relation
    name = models.ForeignKey('Name')
    #: The :py:class:`Researcher` to which the name is attributed
    researcher = models.ForeignKey('Researcher')
    #: The similarity score between this name and one of the reference names for this researcher
    confidence = models.FloatField(default=1.)
    unique_together = (('name','researcher'),)

class Researcher(models.Model):
    """
    A model to represent a researcher
    """

    #: The preferred :py:class:`Name` for this researcher
    name = models.ForeignKey('Name')
    #: It can be associated to a user
    user = models.ForeignKey(User, null=True, blank=True)
   
    # Various info about the researcher (not used internally)
    #: Email address for this researcher
    email = models.EmailField(blank=True,null=True)
    #: URL of the homepage
    homepage = models.URLField(blank=True, null=True)
    #: Grade (student, post-doc, professor…)
    role = models.CharField(max_length=128, null=True, blank=True)
    #: ORCiD identifier
    orcid = models.CharField(max_length=32, null=True, blank=True, unique=True)
    # TODO This could be a custom field as we know what format to expect
    #: Did we manage to import at least one record from the ORCID profile? (Null if we have not tried)
    empty_orcid_profile = models.NullBooleanField()

    # Fetching
    #: Last time we harvested publications for this researcher
    last_harvest = models.DateTimeField(null=True, blank=True)
    #: Task id of the harvester (if any)
    harvester = models.CharField(max_length=512, null=True, blank=True)
    #: Current subtask of the harvester
    current_task = models.CharField(max_length=64, choices=HARVESTER_TASK_CHOICES, null=True, blank=True)

    def __unicode__(self):
        if self.name_id:
            return unicode(self.name)
        else:
            return 'Unnamed researcher'

    @property
    def authors_by_year(self):
        """:py:class:`Author` objects for this researcher, filtered by decreasing publication date"""
        return Author.objects.filter(name__researcher_id=self.id).order_by('-paper__pubdate')
    @property
    def name_variants(self):
        """
        All the names found in papers that could belong to the researcher.
        Among these names, at least the preferred :py:attr:`name`
        should have confidence 1.0 (other names can have confidence 1.0 if 
        multiple names are known. The other names have been found in publications
        and are similar to one of these 1.0 confidence name variants.
        """
        return NameVariant.objects.filter(researcher=self)

    def variants_queryset(self):
        """
        The set of names with the same last name. This is a larger approximation
        than the actual name variants to keep the SQL query simple. The method
        `update_variants` filters out the candidates which are not compatible with the reference
        name.

        .. todo::
            This should rather rely on the name variants with confidence 1.0
        """
        return Name.objects.filter(last__iexact=self.name.last)

    def update_variants(self, reset=False):
        """
        Sets the variants of this name to the candidates returned by variants_queryset
        and which have a positive name similarity with the reference name.

        .. todo::
            This should rather rely on the name variants with confidence 1.0
        """
        nvqs = NameVariant.objects.filter(researcher=self)
        if reset:
            nvqs.delete()
            current_name_variants = set()
        else:
            current_name_variants = set([nv.name_id for nv in nvqs])

        last = self.name.last
        for name in self.variants_queryset():
            sim = name_similarity((name.first,name.last),(self.name.first,self.name.last))
            if sim > 0 and name.id not in current_name_variants:
                self.add_name_variant(name, sim, force_update=reset)

    def add_name_variant(self, name, confidence, force_update=False):
        """
        Add a name variant with the given confidence and update
        the best_confidence field of the name accordingly.

        :param force_update: set the best_confidence even if the current value is
            higher.
        """
        if name.id is None:
            name.save()
        nv = NameVariant.objects.get_or_create(
                name=name, researcher=self, defaults={'confidence':confidence})
        if name.best_confidence < confidence or force_update:
            name.best_confidence = confidence
            name.save(update_fields=['best_confidence'])

    stats = models.ForeignKey(AccessStatistics, null=True)
    def update_stats(self):
        """Update the access statistics for the papers authored by this researcher"""
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(author__researcher=self).distinct())

    def fetch_everything(self):
        # TODO ensure the task is run only once per researcher
        self.harvester = send_task('fetch_everything_for_researcher', [], {'pk':self.id}).id
        self.current_task = 'init' 
        self.save(update_fields=['harvester','current_task'])

    def fetch_everything_if_outdated(self):
        if self.last_harvest is None or timezone.now() - self.last_harvest > PROFILE_REFRESH_ON_LOGIN:
            self.fetch_everything()

    def init_from_orcid(self):
        self.harvester = send_task('init_profile_from_orcid', [], {'pk':self.id}).id
        self.current_task = 'init'
        self.save(update_fields=['harvester', 'current_task'])

    @classmethod
    def get_or_create_by_orcid(cls, orcid, profile=None, user=None):
        researcher = None
        try:
            researcher = Researcher.objects.get(orcid=orcid)
        except Researcher.DoesNotExist:
            if profile is None:
                profile = get_orcid_profile(orcid) 
            name = get_name_from_orcid_profile(profile)
            homepage = get_homepage_from_orcid_profile(profile)
            email = get_email_from_orcid_profile(profile)
            researcher = Researcher.create_from_scratch(name[0],name[1], orcid=orcid,
                    user=user, homepage=homepage, email=email)
            for variant in get_other_names_from_orcid_profile(profile):
                confidence = name_similarity(variant, variant)
                name = Name.lookup_name(variant)
                researcher.add_name_variant(name, confidence)

        return researcher

    @classmethod
    def get_or_create_by_name(cls, first, last, **kwargs):
       name, created = Name.get_or_create(first, last)
       researcher, created = Researcher.objects.get_or_create(name=name, defaults=kwargs)
       if created:
           researcher.update_variants()
           researcher.update_stats()
       return researcher

    @classmethod
    def create_from_scratch(cls, first, last, **kwargs):
        """Creates a researcher, creating first the :py:class:`Name` for it.

        :raises ValueError: if a researcher with that name already exists,
                            or if an invalid ORCiD is provided.
        :raises DataError: if a researcher with that ORCiD already exists.
        """
        name, created = Name.get_or_create(first, last)
        if not created and cls.objects.filter(name=name).count() > 0:
            # we forbid the creation of two researchers with the same name,
            # although our model would support it (TODO ?)
            raise ValueError

        if kwargs.get('orcid') is not None:
            orcid = validate_orcid(kwargs['orcid'])
            if orcid is None:
                raise ValueError('Invalid ORCiD: "%s"' % orcid)

        researcher = Researcher(name=name, **kwargs)
        # This will raise DataError if such an ORCiD already exists
        researcher.save()
        researcher.update_variants()
        researcher.update_stats()
        return researcher
    
    @property
    def object_id(self):
        """Criteria to use in the search view to filter on this researcher"""
        return "researcher=%d" % self.pk


MAX_NAME_LENGTH = 256
class Name(models.Model):
    first = models.CharField(max_length=MAX_NAME_LENGTH)
    last = models.CharField(max_length=MAX_NAME_LENGTH)
    full = models.CharField(max_length=MAX_NAME_LENGTH*2+1, db_index=True)
    best_confidence = models.FloatField(default=0.)

    unique_together = ('first','last')
    
    class Meta:
        ordering = ['last','first']

    @property
    def is_known(self):
        return self.best_confidence > 0.

    @classmethod
    def create(cls, first, last):
        """
        Creates an instance of the Name object without saving it.
        Useful for name lookups where we are not sure we want to
        keep the name in the model.
        """
        first = sanitize_html(first[:MAX_NAME_LENGTH].strip())
        last = sanitize_html(last[:MAX_NAME_LENGTH].strip())
        full = iunaccent(first+' '+last)
        return cls(first=first,last=last,full=full)
    @classmethod
    def get_or_create(cls, first, last):
        """
        Replacement for the regular get_or_create, so that the full
        name is built based on first and last
        """
        first = first.strip()
        last = last.strip()
        full = iunaccent(first+' '+last)
        return cls.objects.get_or_create(full=full, defaults={'first':first,'last':last})
    def variants_queryset(self):
        """
        Returns the queryset of should-be variants.
        WARNING: This is to be used on a name that is already associated with a researcher.
        """
        # TODO this could be refined (icontains?)
        return Researcher.objects.filter(name__last__iexact = self.last)

    def update_variants(self):
        """
        Sets the variants of this name to the candidates returned by variants_queryset
        """
        for researcher in self.variants_queryset():
            sim = name_similarity((researcher.name.first,researcher.name.last), (self.first,self.last))
            if sim > 0:
                old_sim = self.best_confidence
                self.best_confidence = sim
                if self.pk is None or old_sim < sim:
                    self.save()
                NameVariant.objects.get_or_create(name=self,researcher=researcher,
                        defaults={'confidence':sim})

    def update_best_confidence(self):
        """
        A name is considered as known when it belongs to a name variants group of a researcher
        """
        new_value = max([0.]+[d['confidence'] for d in self.namevariant_set.all().values('confidence')])
        if new_value != self.best_confidence:
            self.best_confidence = new_value
            self.save(update_fields=['best_confidence'])

    @classmethod
    def lookup_name(cls, author_name):
        if author_name == None:
            return
        first_name = sanitize_html(author_name[0][:MAX_NAME_LENGTH].strip())
        last_name = sanitize_html(author_name[1][:MAX_NAME_LENGTH].strip())

        # First, check if the name itself is known
        # (we do not take the first/last separation into account
        # here because the exact match is already a quite strong
        # condition)
        full_name = first_name+' '+last_name
        normalized = iunaccent(full_name)
        name = cls.objects.filter(full=normalized).first()
        if name:
            return name

        # Otherwise, we create a name
        name = cls.create(first_name,last_name)
        # The name is not saved yet: the name has to be saved only
        # if the paper is saved or it is a variant of a known name

        # Then, we look for known names with the same last name.
        similar_researchers = Researcher.objects.filter(
                name__last__iexact=last_name).select_related('name')

        name.update_variants()

        return name

    # Used to save unsaved names after lookup
    def save_if_not_saved(self):
        if not self.pk:
            # the best_confidence field should already be up to date as it is computed in the lookup
            self.save()
            self.update_variants()

    def __unicode__(self):
        return '%s %s' % (self.first,self.last)

    def first_letter(self):
        return self.last[0]

    @property
    def object_id(self):
        """Criteria to use in the search view to filter on this name"""
        return "name=%d" % self.pk

# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64)
    date_last_ask = models.DateField(null=True)
    # Approximate publication date.
    # For instance if we only know it is in 2014 we'll put 2014-01-01
    pubdate = models.DateField()

    last_modified = models.DateField(auto_now=True)
    visibility = models.CharField(max_length=32, default='VISIBLE')
    last_annotation = models.CharField(max_length=32, null=True, blank=True)

    doctype = models.CharField(max_length=32, null=True, blank=True)

    def __unicode__(self):
        return self.title

    # The two following fields need to be updated after the relevant changes
    # using the methods below.
    oa_status = models.CharField(max_length=32, null=True, blank=True, default='UNK')
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)

    cached_author_count = None
    nb_remaining_authors = None

    def already_asked_for_upload(self):
        if self.date_last_ask == None:
            return False
        else: 
            return ((datetime.now().date() - self.pubdate) <= timedelta(days=10))

    def can_be_asked_for_upload(self):
        return ((self.pdf_url==None) and
                (self.oa_status=='OK') and
                not(self.already_asked_for_upload()) and
                not(self.author_set.filter(researcher__isnull=False)==[]))

    @property
    def year(self):
        """
        Year of publication of the paper
        """
        return self.pubdate.year

    @property
    def prioritary_oai_records(self):
        """
        OAI records from custom sources we trust (positive priority)
        """
        return self.sorted_oai_records.filter(priority__gt=0)

    @property
    def sorted_oai_records(self):
        """
        OAI records sorted by decreasing order of priority
        (lower priority means poorer overall quality of the source).
        """
        return self.oairecord_set.order_by('-priority')

    @property
    def sorted_authors(self):
        """
        The author sorted as they should appear. Their names are pre-fetched.
        """
        return self.author_set.order_by('position').select_related('name')

    def author_names(self):
        """
        The list of Name instances of the authors
        """
        return [a.name for a in self.sorted_authors]

    def bare_author_names(self):
        """
        The list of name pairs (first,last) of the authors
        """
        return [(name.first,name.last) for name in self.author_names()]


    def author_count(self):
        """
        Number of authors. This property is cached in instances to
        avoid repeated COUNT queries.
        """
        if self.cached_author_count == None:
            self.cached_author_count = self.author_set.count()
        return self.cached_author_count

    def has_many_authors(self):
        """
        When the paper has more than 15 authors (arbitrary threshold)
        """
        return self.author_count() > 15

    def interesting_authors(self):
        """
        The list of authors to display when the complete list is too long.
        We display first the authors whose names are known, and then a few ones
        who are unknown.
        """
        lst = (list(self.sorted_authors.filter(name__best_confidence__gt=0))+list(
            self.sorted_authors.filter(name__best_confidence=0))[:3])[:15]
        self.nb_remaining_authors = self.author_count() - len(lst)
        return lst

    def displayed_authors(self):
        """
        Returns the full list of authors if there are not too many of them,
        otherwise returns only the interesting_authors()
        """
        if self.has_many_authors():
            return self.interesting_authors
        else:
            return self.sorted_authors

    @property
    def toggled_visibility(self):
        if self.visibility == 'VISIBLE':
            return 2 # NOT RELEVANT
        return 0 # VISIBLE

    # TODO: use only codes or only strings, but this is UGLY!
    @property
    def visibility_code(self):
        idx = 0
        for code, lbl in VISIBILITY_CHOICES:
            if code == self.visibility:
                return idx
            idx += 1
        return idx

    # TODO: use only codes or only strings, but this is UGLY!
    @property
    def annotation_code(self):
        idx = 0
        for code, lbl in VISIBILITY_CHOICES:
            if code == self.last_annotation:
                return idx
            idx += 1
        return idx

    @property
    def is_deposited(self):
        return self.successful_deposits().count() > 0

    def update_availability(self):
        # TODO: create an oa_status field in each publication so that we optimize queries
        # and can deal with hybrid OA
        self.pdf_url = None
        publis = self.publication_set.all()
        oa_idx = len(OA_STATUS_PREFERENCE)-1
        type_idx = len(PAPER_TYPE_PREFERENCE)-1
        if self.doctype in PAPER_TYPE_PREFERENCE:
            type_idx = PAPER_TYPE_PREFERENCE.index(self.doctype)
        for publi in publis:
            # OA status
            cur_status = publi.oa_status()
            try:
                idx = OA_STATUS_PREFERENCE.index(cur_status)
            except ValueError:
                idx = len(OA_STATUS_PREFERENCE)
            oa_idx = min(idx, oa_idx)
            if OA_STATUS_CHOICES[oa_idx][0] == 'OA':
                self.pdf_url = publi.splash_url()

            # Pub type
            cur_type = publi.pubtype
            try:
                idx = PAPER_TYPE_PREFERENCE.index(cur_type)
            except ValueError:
                idx = len(PAPER_TYPE_PREFERENCE)
            type_idx = min(idx, type_idx)

        self.oa_status = OA_STATUS_CHOICES[oa_idx][0]
        if not self.pdf_url:
            matches = self.oairecord_set.all().order_by(
                            '-source__oa', '-source__priority').select_related('source')
            self.pdf_url = None
            for m in matches:
                if not self.pdf_url:
                    self.pdf_url = m.pdf_url

                if m.source.oa:
                    self.oa_status = 'OA'
                    if not self.pdf_url:
                        self.pdf_url = m.splash_url

                if m.pubtype in PAPER_TYPE_PREFERENCE:
                    new_idx = PAPER_TYPE_PREFERENCE.index(m.pubtype)
                    type_idx = min(new_idx, type_idx)

        self.doctype = PAPER_TYPE_PREFERENCE[type_idx]
        self.save()
        self.invalidate_cache()

    def status_helptext(self):
        """
        Helptext displayed next to the paper logo
        """
        if self.oa_status == 'OA':
            return _('This paper is made freely available by the publisher.')
        if self.pdf_url is not None:
            return _('This paper is available in a repository.')
        if self.oa_status == 'OK' and self.pdf_url is None:
            return _('This paper was not found in any repository, but could be made available legally by the author.')
        if self.oa_status == 'NOK':
            return _('The publisher of this paper forbids its archiving.')
        if self.oa_status == 'UNK':
            return _('This paper was not found in any repository; the policy of its publisher is unknown or unclear.')

    def publications_with_unique_publisher(self):
        seen_publishers = set()
        for publication in self.publication_set.all():
            if publication.publisher_id and publication.publisher_id not in seen_publishers:
                seen_publishers.add(publication.publisher_id)
                yield publication
            elif publication.publisher_name not in seen_publishers:
                seen_publishers.add(publication.publisher_name)
                yield publication

    def publisher(self):
        for publication in self.publication_set.all():
            return publication.publisher_or_default()
        return DummyPublisher()

    def successful_deposits(self):
        return self.depositrecord_set.filter(pdf_url__isnull=False)
    
    def abstract(self):
        for rec in self.publication_set.all():
            if rec.abstract:
                return rec.abstract
        best_abstract = ''
        for rec in self.oairecord_set.all():
            if rec.description and len(rec.description) > len(best_abstract):
                best_abstract = rec.description
        return best_abstract

    def plain_fingerprint(self, verbose=False):
        """
        Debugging function to display the plain fingerprint
        """
        fp = create_paper_plain_fingerprint(self.title, self.bare_author_names(), self.year)
        if verbose:
            print fp
        return fp

    def new_fingerprint(self, verbose=False):
        buf = self.plain_fingerprint(verbose)
        m = hashlib.md5()
        m.update(buf)
        return m.hexdigest()

    def invalidate_cache(self):
        """
        Invalidate the HTML cache for all the publications of this researcher.
        """
        for rpk in [a.researcher_id for a in self.author_set.filter(researcher_id__isnull=False)]+[None]:
            key = make_template_fragment_key('publiListItem', [self.pk, rpk])
            cache.delete(key)

    def update_author_names(self, new_author_names, new_affiliations=None):
        """
        Improves the current list of authors by considering a new list of author names.
        Missing authors are added, and names are unified.
        If affiliations are provided, they will replace the old ones if they are
        more informative.

        :param new_author_names: list of Name instances (the order matters)
        :param new_affiliations: (optional) list of affiliation strings for the new author names.
        """
        if new_affiliations is None:
            new_affiliations = [None]*len(new_author_names)
        assert len(new_author_names) == len(new_affiliations)
        old_authors = self.sorted_authors
        old_names = map(lambda a: (a.name.first,a.name.last), old_authors)
        unified_names = unify_name_lists(old_names, new_author_names)
        for i, (new_name, (idx,new_idx)) in enumerate(unified_names):
            if idx is not None: # Updating the name of an existing author
                author = old_authors[idx]
                if new_name is None:
                    # Delete that author, it was pruned because it already
                    # appears elsewhere
                    author.delete()
                    continue
                fields = []
                if idx != i:
                    author.position = i
                    fields.append('position')
                if new_name != (author.name.first,author.name.last):
                    name = Name.lookup_name(new_name)
                    name.save()
                    author.name = name
                    fields.append('name')
                if new_idx is not None and affiliation_is_greater(new_affiliations[new_idx], author.affiliation):
                    author.affiliation = new_affiliations[new_idx]
                    fields.append('affiliation')
                    author.update_name_variants_if_needed()
                if fields:
                    author.save(update_fields=fields)
            elif new_name is not None: # Creating a new author
                name = Name.lookup_name(new_name)
                name.save()
                # TODO maybe we could cluster it ? -> move this code to the backend?
                author = Author(paper=self,name=name,position=i,affiliation=new_affiliations[new_idx])
                author.save()

    # Merge paper into self
    def merge(self, paper):
        """
        Merges another paper into self. This deletes the other paper.
        We do our best to unify all the metadata parts, but of course
        there will always be some mistakes as there is no way to find out
        which metadata part is best in general.

        :param paper: The second paper to merge and delete.
        """

        if self.pk == paper.pk:
            return

        statuses = [self.visibility,paper.visibility]
        new_status = 'DELETED'
        for s in VISIBILITY_CHOICES:
            if s[0] in statuses:
                new_status = s[0]
                break
        
        OaiRecord.objects.filter(about=paper.pk).update(about=self.pk)
        Publication.objects.filter(paper=paper.pk).update(paper=self.pk)
        Annotation.objects.filter(paper=paper.pk).update(paper=self.pk)
        self.update_author_names(map(lambda n: (n.first,n.last), paper.author_names()))
        if paper.last_annotation:
            self.last_annotation = None
            for annot in self.annotation_set.all().order_by('-timestamp'):
                self.last_annotation = annot.status
                break
            self.save(update_fields=['last_annotation'])
        paper.invalidate_cache()
        paper.delete()
        self.visibility = new_status
        self.update_availability()


    def recompute_fingerprint_and_merge_if_needed(self):
        new_fingerprint = self.new_fingerprint()
        if self.fingerprint == new_fingerprint:
            return
        match = Paper.objects.filter(fingerprint=new_fingerprint).first()
        if match is None:
            self.fingerprint = new_fingerprint
            self.save(update_fields=['fingerprint'])
            return
        else:
            match.merge(self)
            return match

    def update_visibility(self, prefetched_authors_field=None):
        p = self
        if p.visibility != 'VISIBLE' and p.visibility != 'NOT_RELEVANT':
            return
        researcher_found = False
        if prefetched_authors_field:
            authors = p.__dict__[prefetched_authors_field]
        else:
            authors = p.author_set.all()
        for a in authors:
            if a.researcher_id:
                researcher_found = True
                break
        if researcher_found and p.visibility != 'VISIBLE':
            p.visibility = 'VISIBLE'
            p.save(update_fields=['visibility'])
        elif not researcher_found and p.visibility != 'NOT_RELEVANT':
            p.visibility = 'NOT_RELEVANT'
            p.save(update_fields=['visibility'])

    def google_scholar_link(self):
        """
        Link to search for the paper in Google Scholar
        """
        return 'http://scholar.google.com/scholar?'+urlencode({'q':remove_diacritics(self.title)})

    def core_link(self):
        """
        Link to search for the paper in CORE
        """
        return 'http://core.ac.uk/search/'+quote(remove_diacritics(self.title))

    def is_orphan(self):
        """
        When no publication or OAI record is associated with this paper.
        """
        return (self.oairecord_set.count() == 0 and self.publication_set.count() == 0)



# Researcher / Paper binary relation
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    name = models.ForeignKey(Name)
    position = models.IntegerField(default=0)
    cluster = models.ForeignKey('Author', blank=True, null=True, related_name='clusterrel')
    num_children = models.IntegerField(default=1)
    cluster_relevance = models.FloatField(default=0) # TODO change this default to a negative value
    similar = models.ForeignKey('Author', blank=True, null=True, related_name='similarrel')
    researcher = models.ForeignKey(Researcher, blank=True, null=True, on_delete=models.SET_NULL)

    affiliation = models.CharField(max_length=512, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)
    def orcid(self):
        """
        If the affiliation looks like an ORCiD, return it, otherwise None
        """
        return validate_orcid(self.affiliation)

    def get_cluster_id(self):
        """
        This is the "find" in "Union Find".
        """
        if not self.cluster:
            return self.id
        elif self.cluster_id != self.id: # it is supposed to be the case
            result = self.cluster.get_cluster_id()
            if result != self.cluster_id:
                self.cluster_id = result
                self.save(update_fields=['cluster_id'])
            return result
        raise ValueError('Invalid cluster id (loop)')

    def get_cluster(self):
        i = self.get_cluster_id()
        if i != self.id:
            return Author.objects.get(pk=i)
        return self

    def merge_with(self, author):
        """
        Merges the clusters of two authors
        """
        cur_cluster_id = self.get_cluster_id()
        if cur_cluster_id != self.id:
            cur_cluster = Author.objects.get(pk=cur_cluster_id)
        else:
            cur_cluster = self
        new_cluster_id = author.get_cluster_id()
        if cur_cluster_id != new_cluster_id:
            new_cluster = Author.objects.get(pk=new_cluster_id)
            cur_cluster.cluster = new_cluster
            cur_cluster.save(update_fields=['cluster'])
            new_cluster.num_children += cur_cluster.num_children
            if not new_cluster.researcher and cur_cluster.researcher:
                new_cluster.researcher = cur_cluster.researcher
            new_cluster.save(update_fields=['num_children', 'researcher'])

    def flatten_cluster(self, upstream_root=None):
        """
        Flattens the cluster rooted in self, using upstream_root if provided,
        or as the root if None
        """
        if not upstream_root:
            upstream_root = self
        else:
            self.cluster = upstream_root
            if upstream_root.researcher:
                self.researcher = upstream_root.researcher()
            self.save()
        children = self.clusterrel_set.all()
        for child in children:
            child.flatten_cluster(upstream_root)

    @property
    def is_known(self):
        return self.researcher != None

    @property
    def orcid(self):
        return validate_orcid(self.affiliation)

    def update_name_variants_if_needed(self, default_confidence=0.1):
        """
        Ensure that an author associated with an ORCID has a name
        that is the variant of the researcher with that ORCID
        """
        orcid = self.orcid
        if orcid:
            try:
                r = Researcher.objects.get(orcid=orcid)
                nv = NameVariant.objects.get_or_create(
                        researcher=r,
                        name=self.name,
                        defaults={'confidence':default_confidence})
            except Researcher.DoesNotExist:
                pass

# Publication of these papers (in journals or conference proceedings)
class Publication(models.Model):
    # TODO prepare this model for user input (allow for other URLs than DOIs)
    paper = models.ForeignKey(Paper)
    pubtype = models.CharField(max_length=64)

    title = models.CharField(max_length=512) # this is actually the *journal* title
    journal = models.ForeignKey(Journal, blank=True, null=True)
    container = models.CharField(max_length=512, blank=True, null=True)

    publisher = models.ForeignKey(Publisher, blank=True, null=True)
    publisher_name = models.CharField(max_length=512, blank=True, null=True)

    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    pubdate = models.DateField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)

    doi = models.CharField(max_length=1024, unique=True, blank=True, null=True) # in theory, there is no limit

    def oa_status(self):
        if self.publisher:
            return self.publisher.oa_status
        else:
            return 'UNK'

    def splash_url(self):
        if self.doi:
            return 'http://dx.doi.org/'+self.doi

    def full_title(self):
        if self.journal:
            return self.journal.title
        else:
            return self.title

    def publisher_or_default(self):
        if self.publisher_id:
            return self.publisher
        if self.publisher_name:
            return DummyPublisher(self.publisher_name)
        return DummyPublisher()

    def details_to_str(self):
        result = ''
        if self.issue or self.volume or self.pages or self.pubdate:
            result += ', '
        if self.issue:
            result += self.issue
        if self.volume:
            result += '('+self.volume+')'
        if self.issue or self.volume:
            result += ', '
        if self.pages:
            result += self.pages+', '
        if self.pubdate:
            result += str(self.pubdate.year)
        return result

    def __unicode__(self):
        return self.title+self.details_to_str()

# Rough data extracted through OAI-PMH
class OaiSource(models.Model):
    identifier = models.CharField(max_length=300, unique=True)
    name = models.CharField(max_length=100)
    oa = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)
    default_pubtype = models.CharField(max_length=128)

    # Fetching properties
    last_status_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "OAI source"

class OaiRecord(models.Model):
    source = models.ForeignKey(OaiSource)
    about = models.ForeignKey(Paper)

    identifier = models.CharField(max_length=512, unique=True)
    splash_url = models.URLField(max_length=1024, null=True, blank=True)
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)
    description = models.TextField(null=True,blank=True)
    keywords = models.TextField(null=True,blank=True)
    contributors = models.CharField(max_length=4096, null=True, blank=True)
    pubtype = models.CharField(max_length=512, null=True, blank=True)

    # Cached version of source.priority
    priority = models.IntegerField(default=1)
    def update_priority(self):
        self.priority = self.source.priority
        self.save(update_fields=['priority'])

    last_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.identifier

    @classmethod
    def new(cls, **kwargs):
        if kwargs.get('source') is None:
            raise ValueError('No source provided to create the OAI record.')
        source = kwargs['source']
        if kwargs.get('identifier') is None:
            raise ValueError('No identifier provided to create the OAI record.')
        identifier = kwargs['identifier']
        if kwargs.get('about') is None:
            raise ValueError('No paper provided to create the OAI record.')
        about = kwargs['about']
        if kwargs.get('splash_url') is None:
            raise ValueError('No URL provided to create the OAI record.')
        splash_url = kwargs['splash_url']

        # Search for duplicate records
        pdf_url = kwargs.get('pdf_url')
        match = OaiRecord.find_duplicate_records(source, identifier, about, splash_url, pdf_url)

        # Update the duplicate if necessary
        if match:
            changed = False

            if pdf_url != None and (match.pdf_url == None or
                    (match.pdf_url != pdf_url and match.priority < source.priority)):
                match.source = source
                match.priority = source.priority
                match.pdf_url = pdf_url
                match.splash_url = splash_url
                changed = True

            def update_field_conditionally(field):
                new_val = kwargs.get(field, '')
                if new_val and (not match.__dict__[field] or
                        len(match.__dict__[field]) < len(new_val)):
                    match.__dict__[field] = new_val
                    changed = True
            
            update_field_conditionally('contributors')
            update_field_conditionally('keywords')
            update_field_conditionally('description')

            new_pubtype = kwargs.get('pubtype', source.default_pubtype)
            if new_pubtype in PAPER_TYPE_PREFERENCE:
                idx = PAPER_TYPE_PREFERENCE.index(new_pubtype)
                old_idx = len(PAPER_TYPE_PREFERENCE)-1
                if match.pubtype in PAPER_TYPE_PREFERENCE:
                    old_idx = PAPER_TYPE_PREFERENCE.index(match.pubtype)
                if idx < old_idx:
                    changed = True
                    match.pubtype = PAPER_TYPE_PREFERENCE[idx]
                
            if changed:
                try:
                    match.save()
                except DataError as e:
                    raise ValueError('Unable to create OAI record:\n'+unicode(e))

            if about.pk != match.about.pk:
                about.merge(match.about)

            match.about.update_availability()
            return match

        # Otherwise create a new record
        record = OaiRecord(
                source=source,
                identifier=identifier,
                splash_url=splash_url,
                pdf_url=pdf_url,
                about=about,
                description=kwargs.get('description'),
                keywords=kwargs.get('keywords'),
                contributors=kwargs.get('contributors'),
                pubtype=kwargs.get('pubtype', source.default_pubtype),
                priority=source.priority)
        record.save()

        about.update_availability()
        return record
    
    @classmethod
    def find_duplicate_records(cls, source, identifier, about, splash_url, pdf_url):
        https_re = re.compile(r'https?(.*)')
        exact_dups = OaiRecord.objects.filter(identifier=identifier)
        if exact_dups:
            return exact_dups[0]
        
        def shorten(url):
            if not url:
                return
            match = https_re.match(url.strip())
            if not match:
                print "Warning, invalid URL: "+url
            return match.group(1)

        short_splash = shorten(splash_url)
        short_pdf = shorten(pdf_url)

        if splash_url == None or about == None:
            return

        if pdf_url == None:
            matches = OaiRecord.objects.filter(about=about,
                    splash_url__endswith=short_splash)
            if matches:
                return matches[0]
        else:
            matches = OaiRecord.objects.filter(
                    Q(splash_url__endswith=short_splash) |
                    Q(pdf_url__endswith=short_pdf) |
                    Q(pdf_url__isnull=True), about=about)[:1]
            for m in matches:
                return m

    class Meta:
        verbose_name = "OAI record"

# A singleton to link to a special instance of AccessStatistics for all papers
class PaperWorld(SingletonModel):
    stats = models.ForeignKey(AccessStatistics, null=True)

    def update_stats(self):
        """Update the access statistics for all papers"""
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.all())

    @property
    def object_id(self):
        return ''

    def __unicode__(self):
        return "All papers"

    class Meta:
        verbose_name = "Paper World"

# Annotation tool to train the models
class Annotation(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    timestamp = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.user)+': '+self.status
    @classmethod
    def create(self, paper, status, user): 
        annot = Annotation(paper=paper, status=status, user=user)
        annot.save()
        # TODO: we leave paper visibility as is, for the experiment, but this should be changed in the future.
        paper.last_annotation = status
        paper.save(update_fields=['last_annotation'])
        paper.invalidate_cache()


