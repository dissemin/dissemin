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

"""
This module defines most of the models used in the platform.

* :class:`Paper` represents a (deduplicated) paper.
   The sources it has been discovered from are witnessed
   by two types of records:
    * :class:`OaiRecord` instances are created by OAI-PMH sources, or
      metadata sources not originally in OAI-PMH but wrapped in this format
      by proaixy. They indicate the availability of the paper in repositories.
      They link to an :class:`OaiSource` object that indicates what data source
      we have got this record from.
   Multiple :class:`OaiRecord` can (and typically are) associated
   with a paper, when the metadata they contain yield the same paper fingerprint.
   These records are stored inside the Paper object in a JSON field.

* :class:`Researcher` represents a researcher profile (a physical person).
   This person has a cannonical :class:`Name`, but can also be associated with
   other names through a :class:`NameVariant` relation (indicating a confidence value
   for the association of the name with this reseracher).

* :class:`Author` objects represent the occurrence of a :class:`Name` in the author list
   of a :class:`Paper`. When we are confident that this name actually refers to a
   given :class:`Researcher`, the :class:`Author` object has a link to it.
   All the authors that could potentially be associated with a given :class:`Researcher`
   (that is when their name is a :class:`NameVariant` for that researcher) are clustered
   in groups by merging similar authors (i.e. authors associated to similar papers).
   
* Researchers can be organized into :class:`Department` instances, which belong to an
  :class:`Institution`.

"""

from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models import Q
from django.db import DataError
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from solo.models import SingletonModel
from celery.execute import send_task
from celery.result import AsyncResult

from papers.baremodels import *
from papers.name import match_names, name_similarity, unify_name_lists
from papers.utils import remove_diacritics, sanitize_html, validate_orcid, affiliation_is_greater, remove_nones, index_of, iunaccent
from papers.orcid import OrcidProfile

from statistics.models import AccessStatistics, STATUS_CHOICES_HELPTEXT, combined_status_for_instance
from publishers.models import Publisher, Journal, OA_STATUS_CHOICES, OA_STATUS_PREFERENCE, DummyPublisher
from upload.models import UploadedPDF
from dissemin.settings import PROFILE_REFRESH_ON_LOGIN, POSSIBLE_LANGUAGE_CODES

import hashlib, re
from datetime import datetime, timedelta

UPLOAD_TYPE_CHOICES = [
   ('preprint', _('Preprint')),
   ('postprint', _('Postprint')),
   ('pdfversion', _("Published version")),
   ]

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


class Institution(models.Model):
    """
    A university or research institute.
    """
    #: The full name of the institution 
    name = models.CharField(max_length=300)

    #: :py:class:`AccessStatistics` about the papers authored in this institution.
    stats = models.ForeignKey(AccessStatistics, null=True, blank=True)

    @property
    def sorted_departments(self):
        """
        Departments belonging to this institution, sorted by name.
        """
        return self.department_set.order_by('name')

    def __unicode__(self):
        return self.name

    def update_stats(self):
        """
        Refreshes the institution-level access statistics.
        """
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(author__researcher__department__institution=self).distinct())

    @property
    def object_id(self):
        """
        Criteria to use in the search view to filter on this department
        """
        return "institution=%d" % self.pk

    @property
    def url(self):
        """
        The URL of the main page (list of departments for this institution).
        """
        return reverse('institution', args=[self.pk])

    def breadcrumbs(self):
        return [(unicode(self),self.url)]

class Department(models.Model):
    """
    A department in an institution. Each :py:class:`Researcher` is affiliated with exactly one department.
    :param name: the full name of the department
    """

    #: The full name of the department
    name = models.CharField(max_length=300)
    #: The institution it belongs to
    institution = models.ForeignKey(Institution)

    #: :py:class:`AccessStatistics` about the papers authored in this department
    stats = models.ForeignKey(AccessStatistics, null=True, blank=True)

    @property
    def sorted_researchers(self):
        """List of :py:class:`Researcher` in this department sorted by last name (prefetches their stats as well)"""
        return self.researcher_set.select_related('name', 'stats').order_by('name')

    def __unicode__(self):
        return self.name

    def update_stats(self):
        """Refreshes the department-level access statistics for that department."""
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(author__researcher__department=self).distinct())

    @property
    def object_id(self):
        """
        Criteria to use in the search view to filter on this department
        """
        return "department=%d" % self.pk

    @property
    def url(self):
        """
        The URL of the main page (list of researchers) for this department.
        """
        return reverse('department', args=[self.pk])

    def breadcrumbs(self):
        return self.institution.breadcrumbs()+[(unicode(self),self.url)]

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

    class Meta:
        unique_together = (('name','researcher'),)

class Researcher(models.Model):
    """
    A model to represent a researcher
    """

    #: The preferred :py:class:`Name` for this researcher
    name = models.ForeignKey('Name')
    #: It can be associated to a user
    user = models.ForeignKey(User, null=True, blank=True)
    #: It can be affiliated to a department
    department = models.ForeignKey(Department, null=True)

    # Various info about the researcher (not used internally)
    #: Email address for this researcher
    email = models.EmailField(blank=True,null=True)
    #: URL of the homepage
    homepage = models.URLField(blank=True, null=True)
    #: Grade (student, post-doc, professor…)
    role = models.CharField(max_length=128, null=True, blank=True)
    #: ORCiD identifier
    orcid = models.CharField(max_length=32, null=True, blank=True, unique=True)
    #: Did we manage to import at least one record from the ORCID profile? (Null if we have not tried)
    empty_orcid_profile = models.NullBooleanField()

    # Fetching
    #: Last time we harvested publications for this researcher
    last_harvest = models.DateTimeField(null=True, blank=True)
    #: Task id of the harvester (if any)
    harvester = models.CharField(max_length=512, null=True, blank=True)
    #: Current subtask of the harvester
    current_task = models.CharField(max_length=64, choices=HARVESTER_TASK_CHOICES, null=True, blank=True)

    #: Statistics of papers authored by this researcher
    stats = models.ForeignKey(AccessStatistics, null=True)

    @property
    def slug(self):
        return slugify(self.name)

    def __unicode__(self):
        if self.name_id:
            return unicode(self.name)
        else:
            return 'Unnamed researcher'

    @property
    def url(self):
        return reverse('researcher', kwargs={'researcher':self.pk, 'slug':self.slug})

    @property
    def papers(self):
        """
        :py:class:`Paper` objects for this researcher,
        sorted by decreasing publication date
        """
        return Paper.objects.filter(
                authors_list__contains=[{'researcher_id':self.id}]
                          ).order_by('-pubdate')

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
        nvqs = self.namevariant_set.all()
        if reset:
            for nv in nvqs:
                name = nv.name
                nv.delete()
                name.update_best_confidence()

            current_name_variants = set()
        else:
            current_name_variants = set([nv.name_id for nv in nvqs])

        last = self.name.last
        for name in self.variants_queryset():
            sim = name_similarity((name.first,name.last),
                                  (self.name.first,self.name.last))
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

    def update_stats(self):
        """Update the access statistics for the papers authored by this researcher"""
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(self.papers)

    def fetch_everything(self):
        self.harvester = send_task('fetch_everything_for_researcher', [], {'pk':self.id}).id
        self.current_task = 'init' 
        self.save(update_fields=['harvester','current_task'])

    def fetch_everything_if_outdated(self):
        if self.last_harvest is None or timezone.now() - self.last_harvest > PROFILE_REFRESH_ON_LOGIN:
            self.fetch_everything()

    def recluster_batch(self):
        self.harvester = send_task('recluster_researcher', [], {'pk':self.id}).id
        self.current_task = 'clustering'
        self.save(update_fields=['harvester','current_task'])

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
                profile = OrcidProfile(id=orcid) 
            else:
                profile = OrcidProfile(json=profile)
            name = profile.name
            homepage = profile.homepage
            email = profile.email
            researcher = Researcher.create_by_name(name[0],name[1], orcid=orcid,
                    user=user, homepage=homepage, email=email)

            # Ensure that extra info is added.
            save = False
            for kw, val in [('homepage',homepage),('orcid',orcid),('email',email)]:
                if not researcher.__dict__[kw] and val:
                    researcher.__dict__[kw] = val
                    save = True
            if save:
                researcher.save()

            for variant in profile.other_names:
                confidence = name_similarity(variant, variant)
                name = Name.lookup_name(variant)
                researcher.add_name_variant(name, confidence)

        return researcher

    @classmethod
    def create_by_name(cls, first, last, **kwargs):
        """
        Creates a :class:`Researcher` with the given name.
        If an ORCID is provided, and a researcher with this ORCID already exists,
        this researcher will be returned. In any other case, a new researcher will be created.
        """
        name, created = Name.get_or_create(first, last)

        if kwargs.get('orcid') is not None:
            orcid = validate_orcid(kwargs['orcid'])
            if kwargs['orcid'] is None:
                raise ValueError('Invalid ORCiD: "%s"' % orcid)
            researcher, created = Researcher.objects.get_or_create(name=name, orcid=orcid, defaults=kwargs)
        else:
            args = kwargs.copy()
            args['name'] = name
            researcher = Researcher.objects.create(**args)
            created = True

        if created:
            researcher.update_variants()
            researcher.update_stats()
        return researcher

    @property
    def object_id(self):
        """Criteria to use in the search view to filter on this researcher"""
        return "researcher=%d" % self.pk

    def breadcrumbs(self):
        last =  [(unicode(self),reverse('researcher', args=[self.pk]))]
        if not self.department:
            return last
        else:
            return self.department.breadcrumbs()+last

    @cached_property
    def latest_paper(self):
        """
        Returns the latest paper authored by this researcher, if any.
        """
        lst = list(self.authors_by_year[:1])
        if lst:
            return lst[0].paper

    def affiliation_form(self):
        """
        Returns a form to change the affiliation of this researcher
        """
        from papers.forms import ResearcherDepartmentForm
        data = {'pk':self.id,
                'department':self.department_id}
        return ResearcherDepartmentForm(initial=data)

class Name(models.Model, BareName):
    first = models.CharField(max_length=MAX_NAME_LENGTH)
    last = models.CharField(max_length=MAX_NAME_LENGTH)
    full = models.CharField(max_length=MAX_NAME_LENGTH*2+1, db_index=True)
    best_confidence = models.FloatField(default=0.)

    class Meta:
        unique_together = ('first','last')
        ordering = ['last','first']

    @property
    def is_known(self):
        """
        Does this name belong to at least one known :class:`Researcher`?
        """
        return self.best_confidence > 0.

    @classmethod
    def get_or_create(cls, first, last):
        """
        Replacement for the regular get_or_create, so that the full
        name is built based on first and last
        """
        n = cls.create(first, last)
        return cls.objects.get_or_create(full=n.full,
                defaults={'first':n.first,'last':n.last})

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
        """
        Lookup a name (pair of (first,last)) in the model.
        If there is already such a name in the database, returns it,
        otherwise creates one properly.

        In addition to `get_or_create`, this looks for relevant researchers
        whose name might match this one.
        """
        if author_name == None:
            return
        n, created = cls.get_or_create(author_name[0], author_name[1])

        if created or True:
            # Actually, this saves the name if it is relevant
            n.update_variants()

        return n

    @classmethod
    def from_bare(cls, bare_name):
        """
        Calls `lookup_name` for the given `bare_name`, if it is indeed bare..
        """
        if hasattr(bare_name, 'id'):
            return bare_name # not so bare…
        return cls.lookup_name((bare_name.first, bare_name.last))

    def save_if_not_saved(self):
        """
        Used to save unsaved names after lookup
        """
        if self.pk is None:
            # the best_confidence field should already be up to date as it is computed in the lookup
            self.save()
            self.update_variants()

    @property
    def object_id(self):
        """Criteria to use in the search view to filter on this name"""
        return "name=%d" % self.pk


# Papers matching one or more researchers
class Paper(models.Model, BarePaper):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64, unique=True)
    date_last_ask = models.DateField(null=True)
    # Approximate publication date.
    # For instance if we only know it is in 2014 we'll put 2014-01-01
    pubdate = models.DateField()
    authors_list = JSONField()

    last_modified = models.DateField(auto_now=True)
    visibility = models.CharField(max_length=32, default='VISIBLE')
    last_annotation = models.CharField(max_length=32, null=True, blank=True)

    doctype = models.CharField(max_length=64, null=True, blank=True, choices=PAPER_TYPE_CHOICES)

    # The two following fields need to be updated after the relevant changes
    # using the methods below.
    oa_status = models.CharField(max_length=32, null=True, blank=True, default='UNK')
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)

    # Task id of the current task updating the metadata of this article (if any)
    task = models.CharField(max_length=512, null=True, blank=True)


    ### Relations to other models, reimplemented from :class:`BarePaper` ###

    @cached_property
    def authors(self):
        """
        The author sorted as they should appear. Their names are pre-fetched.
        """
        return map(BareAuthor.deserialize, self.authors_list)

    @property
    def publications(self):
        """
        The list of publications associated with this paper, returned
        as a queryset.
        """
        return self.oairecord_set.filter(journal_title__isnull=False,
                publisher_name__isnull=False)

    @property
    def oairecords(self):
        """
        The list of OAI records associated with this paper, returned
        as a queryset.
        """
        return self.oairecord_set.all()

    def add_author(self, author, position=None):
        """
        Add an author at the end of the authors list by default
        or at the specified position.
        
        :param position: add the author at that index.
        """
        author_serialized = author.serialize()
        if position is None:
            position = len(self.authors_list)
        self.authors_list.insert(position, author_serialized)
        self.save(update_field='autors_list')
        return author

    def add_oairecord(self, oairecord):
        """
        Adds a record (possibly bare) to the paper, by saving it in
        the database
        """
        # Test first if there is no publication with this new DOI
        doi = oairecord.doi
        if doi:
            matches = OaiRecord.objects.filter(doi__iexact=doi)
            if matches:
                rec = matches[0]
                if rec.about != self:
                    self.merge(rec.about)
                return rec

        return OaiRecord.new(about=self,
                **oairecord.__dict__)

    ### Paper creation ###

    @classmethod
    def get_or_create(cls, title, author_names, pubdate, visibility='VISIBLE', affiliations=None):
        """
        Creates an (initially) bare paper and saves it to the database.

        :returns: the corresponding :class:`Paper` instance.
        """
        p = BarePaper.create(title, author_names, pubdate, visibility, affiliations)
        return cls.from_bare(p)

    @classmethod
    def from_bare(cls, paper):
        """
        Saves a paper to the database if it is not already present.
        The clustering algorithm is run to decide what authors should be 
        attributed to the paper.

        :returns: the :class:`Paper` instance created from the bare paper supplied.
        """
        try:
            # Look up the fingerprint
            fp = paper.fingerprint
            matches = Paper.objects.filter(fingerprint__exact=fp)

            p = None
            if matches: # We have found a paper matching the fingerprint
                p = matches[0]
                if (paper.visibility == 'VISIBLE' and
                        p.visibility == 'CANDIDATE'):
                    p.visibility ='VISIBLE'
                    p.save(update_fields=['visibility'])
                p.update_author_names(paper.bare_author_names(),
                        paper.affiliations())
                for record in paper.oairecords:
                    p.add_oairecord(record)
            else: # Otherwise we create a new paper
                p = super(Paper, cls).from_bare(paper)
                p.save()
                p.update_availability()
                p.save()

            return p

        except DataError as e:
            raise ValueError('Invalid paper, does not fit in the database schema:\n'+unicode(e))


    ### Other methods, specific to this non-bare subclass ###

    def update_author_stats(self):
        """
        Updates the statistics of all researchers identified for this paper
        """
        for author in self.authors:
            if author.researcher:
                author.researcher.update_stats()

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


    @cached_property
    def owners(self):
        """
        Returns the list of users that own this papers (listed as authors and identified as such).
        """
        users = []
        for a in self.authors:
            if a.researcher and a.researcher.user:
                users.append(a.researcher.user)
        return users

    def is_owned_by(self, user):
        """
        Is this user one of the owners of that paper?
        """
        return user in self.owners

    @property
    def annotation_code(self):
        return index_of(self.last_annotation, VISIBILITY_CHOICES)

    @cached_property
    def is_deposited(self):
        return self.successful_deposits().count() > 0

    def update_availability(self):
        """
        Updates the :class:`Paper`'s own `pdf_url` field
        based on its sources (:class:`OaiRecord`).
        
        This uses a non-trivial logic, hence it is useful to keep this result cached
        in the database row.
        """
        super(Paper, self).update_availability()
        self.save()
        self.invalidate_cache()

    def status_helptext(self):
        """
        Helptext displayed next to the paper logo
        """
        return STATUS_CHOICES_HELPTEXT[self.combined_status]
    
    @property
    def combined_status(self):
        """
        The combined status of the paper (availability and policy)
        """
        return combined_status_for_instance(self)

    def consolidate_metadata(self, wait=True):
        """
        Tries to find an abstract for the paper, if none is available yet,
        possibly by fetching it from Zotero via doi-cache.
        """
        if self.task is None:
            task = send_task('consolidate_paper', [], {'pk':self.id})
            self.task = task.id
            self.save(update_fields=['task'])
        else:
            task = AsyncResult(self.task)
        if wait:
            task.get()

    @classmethod
    def create_by_doi(self, doi, wait=True, bare=False):
        """
        Creates a paper given a DOI (sends a task to the backend).
        """
        if not bare:
            task = send_task('get_paper_by_doi', [], {'doi':doi})
        else:
            import backend.crossref as crossref
            import backend.oai as oai
            oai = oai.OaiPaperSource(max_results=10)
            crps = crossref.CrossRefPaperSource(oai=oai)
            return crps.create_paper_by_doi(doi)

        if wait:
            return task.get()

    def successful_deposits(self):
        return self.depositrecord_set.filter(pdf_url__isnull=False)
    
    def invalidate_cache(self):
        """
        Invalidate the HTML cache for all the publications of this researcher.
        """
        for a in self.authors+[None]:
            rpk = None
            if a:
                if a.researcher_id is None:
                    continue
                else:
                    rpk = a.researcher_id 
            for lang in POSSIBLE_LANGUAGE_CODES:
                key = make_template_fragment_key('publiListItem', [self.pk, lang, rpk])
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
        if hasattr(self, 'authors'):
            del self.authors
        old_authors = list(self.authors)

        # Invalidate cached properties
        if hasattr(self, 'interesting_authors'):
            del self.interesting_authors

        old_names = map(lambda a: (a.name.first,a.name.last), old_authors)
        unified_names = unify_name_lists(old_names, new_author_names)
        seen_old_names = set()
        for i, (new_name, (idx,new_idx)) in enumerate(unified_names):
            if idx is not None: # Updating the name of an existing author
                seen_old_names.add(idx)
                author = old_authors[idx]
                if new_name is None:
                    # Delete that author, it was pruned because it already
                    # appears elsewhere
                    if author.id is not None:
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
                    author.name.save_if_not_saved()
                    author.save()
            elif new_name is not None: # Creating a new author
                name = Name.lookup_name(new_name)
                name.save()
                author = Author(paper=self,name=name,position=i,affiliation=new_affiliations[new_idx])
                author.save()
        
        # Just in case unify_name_lists pruned authors without telling us…
        for idx, author in enumerate(old_authors):
            if idx not in seen_old_names:
                print("** Deleting author %d **" % author.pk)
                author.delete()

        # Invalidate our local cache
        if hasattr(self, 'authors'):
            del self.authors

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
        """
        Recomputes the fingerprint based on the new
        values of the paper's attributes, checks whether
        there is already another paper with the same fingerprint,
        and if so merge them.
        """
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

    def breadcrumbs(self):
        """
        Returns the navigation path to the paper, for display as breadcrumbs in the template.
        """
        first_researcher = None
        for author in self.authors:
            if author.researcher:
                first_researcher = author.researcher
                break
        result = []
        if first_researcher is None:
            result.append((_('Papers'), reverse('search')))
        else:
            result.append((unicode(first_researcher), reverse('researcher', args=[first_researcher.pk])))
        result.append((self.citation, reverse('paper', args=[self.pk])))
        return result

# Rough data extracted through OAI-PMH
class OaiSource(models.Model):
    identifier = models.CharField(max_length=300, unique=True)
    name = models.CharField(max_length=100)
    oa = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)
    default_pubtype = models.CharField(max_length=64, choices=PAPER_TYPE_CHOICES)

    # Fetching properties
    last_status_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "OAI source"

class OaiRecord(models.Model, BareOaiRecord):
    source = models.ForeignKey(OaiSource)
    about = models.ForeignKey(Paper)

    identifier = models.CharField(max_length=512, unique=True)
    splash_url = models.URLField(max_length=1024, null=True, blank=True)
    pdf_url = models.URLField(max_length=1024, null=True, blank=True)
    description = models.TextField(null=True,blank=True)
    keywords = models.TextField(null=True,blank=True)
    contributors = models.CharField(max_length=4096, null=True, blank=True)
    pubtype = models.CharField(max_length=64, null=True, blank=True, choices=PAPER_TYPE_CHOICES)

    journal_title = models.CharField(max_length=512, blank=True, null=True) # this is actually the *journal* title
    container = models.CharField(max_length=512, blank=True, null=True)
    journal = models.ForeignKey(Journal, blank=True, null=True)

    publisher = models.ForeignKey(Publisher, blank=True, null=True)
    publisher_name = models.CharField(max_length=512, blank=True, null=True)

    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    pubdate = models.DateField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)

    doi = models.CharField(max_length=1024, unique=True, blank=True, null=True) # in theory, there is no limit


    last_update = models.DateTimeField(auto_now=True)

    # Cached version of source.priority
    priority = models.IntegerField(default=1)

    def update_priority(self):
        super(OaiRecord, self).update_priority()
        self.save(update_fields=['priority'])

    @classmethod
    def new(cls, **kwargs):
        """
        Creates a new OAI record by checking first for duplicates and 
        updating them if necessary.
        """
        source = None
        if kwargs.get('source') is None:
            source_id = kwargs.get('source_id')
            try:
                source = OaiSource.objects.get(id=source_id)
            except ObjectDoesNotExist:
                pass
            if source is None:
                raise ValueError('No source provided to create the OAI record.')
        else:
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
        match = OaiRecord.find_duplicate_records(
                identifier,
                about,
                splash_url,
                pdf_url)

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
                priority=source.priority,
                journal_title=kwargs.get('journal_title'),
                container=kwargs.get('container'),
                publisher_name=kwargs.get('publisher_name'),
                issue=kwargs.get('issue'),
                volume=kwargs.get('volume'),
                pages=kwargs.get('pages'),
                doi=kwargs.get('doi'),
                publisher=kwargs.get('publisher'),
                journal=kwargs.get('journal'),
                )
        record.save()

        about.update_availability()
        return record
    
    @classmethod
    def find_duplicate_records(cls, identifier, about, splash_url, pdf_url):
        """
        Finds duplicate OAI records. These duplicates can have a different identifier,
        or slightly different urls (for instance https:// instead of http://).
        
        :param identifier: the identifier of the target record: if there is one with the same
            identifier, it will be returned
        :param about: the :class:`Paper` the record is about
        :param splash_url: the splash url of the target record (link to the metadata page)
        :param pdf_url: the url of the PDF, if known (otherwise `None`)
        """
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
            else:
                return match.group(1)

        short_splash = shorten(splash_url)
        short_pdf = shorten(pdf_url)

        if short_splash == None or about == None:
            return

        if short_pdf == None:
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

class PaperWorld(SingletonModel):
    """
    A singleton to link to a special instance of AccessStatistics for all papers
    """
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

class Annotation(models.Model):
    """
    Annotation tool to train the models
    """
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



