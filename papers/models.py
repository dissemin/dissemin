# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from papers.utils import nstr, iunaccent, create_paper_plain_fingerprint
from papers.name import match_names
from papers.utils import remove_diacritics
from django.utils.translation import ugettext_lazy as _
import hashlib
from datetime import datetime, timedelta
from urllib import urlencode, quote # for the Google Scholar and CORE link

OA_STATUS_CHOICES = (
        ('OA', _('Open access')),
        ('OK', _('Allows pre/post prints')),
        ('NOK', _('Forbids pre/post prints')),
        ('UNK', _('Policy unclear')),
   )

OA_STATUS_PREFERENCE = ['OA','OK','NOK','UNK']

PDF_STATUS_CHOICES = [('OK', _('Available')),
                      ('NOK', _('Unavailable'))]

VISIBILITY_CHOICES = [('VISIBLE', _('Visible')),
                      ('CANDIDATE', _('Candidate')),
                      ('NOT_RELEVANT', _('Not relevant')),
                      ('DELETED', _('Deleted')),
                      ]

POLICY_CHOICES = [('can', _('Allowed')),
                  ('cannot', _('Forbidden')),
                  ('restricted', _('Restricted')),
                  ('unclear', _('Unclear')),
                  ('unknown', _('Unknown'))]

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

PAPER_TYPE_PREFERENCE = [x for (x,y) in PAPER_TYPE_CHOICES]

class AccessStatistics(models.Model):
    """
    Caches numbers of papers in different access statuses for some queryset
    """
    num_oa = models.IntegerField(default=0)
    num_ok = models.IntegerField(default=0)
    num_couldbe = models.IntegerField(default=0)
    num_unk = models.IntegerField(default=0)
    num_closed = models.IntegerField(default=0)
    num_tot = models.IntegerField(default=0)

    def update(self, queryset):
        """
        Updates the statistics for papers contained in the given Paper queryset
        """
        queryset = queryset.filter(visibility="VISIBLE")
        self.num_oa = queryset.filter(oa_status='OA').count()
        self.num_ok = queryset.filter(pdf_url__isnull=False).count() - self.num_oa
        self.num_couldbe = queryset.filter(pdf_url__isnull=True, oa_status='OK').count()
        self.num_unk = queryset.filter(pdf_url__isnull=True, oa_status='UNK').count()
        self.num_closed = queryset.filter(pdf_url__isnull=True, oa_status='NOK').count()
        self.num_tot = queryset.count()
        self.save()

    @property
    def percentage_oa(self):
        if self.num_tot:
            return int(100.*self.num_oa/self.num_tot)
    @property
    def percentage_ok(self):
        if self.num_tot:
            return int(100.*self.num_ok/self.num_tot)
    @property
    def percentage_couldbe(self):
        if self.num_tot:
            return int(100.*self.num_couldbe/self.num_tot)
    @property
    def percentage_unk(self):
        return 100 - (self.percentage_oa + self.percentage_ok +
            self.percentage_closed + self.percentage_couldbe)
    @property
    def percentage_closed(self):
        if self.num_tot:
            return int(100.*self.num_closed/self.num_tot)

    @classmethod
    def update_all_stats(self, _class):
        for x in _class.objects.all():
            x.update_stats()

# Information about the researchers and their groups
class Department(models.Model):
    name = models.CharField(max_length=300)

    stats = models.ForeignKey(AccessStatistics, null=True)

    @property
    def sorted_researchers(self):
        return self.researcher_set.select_related('name', 'stats').order_by('name')

    def __unicode__(self):
        return self.name

    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(author__researcher__department=self).distinct())

class ResearchGroup(models.Model):
    name = models.CharField(max_length=300)

    def __unicode__(self):
        return self.name

class Researcher(models.Model):
    # The preferred name for this researcher
    name = models.ForeignKey('Name')
    # Variants of this name found in the papers
    name_variants = models.ManyToManyField('Name', related_name='variant_of')
    # Department the researcher belongs to
    department = models.ForeignKey(Department)
    # Research groups the researcher belongs to
    groups = models.ManyToManyField(ResearchGroup)
    
    # Various info about the researcher (not used internally)
    email = models.EmailField(blank=True,null=True)
    homepage = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=128, null=True, blank=True)

    # DOI search
    # TODO is this still needed ?
    last_doi_search = models.DateTimeField(null=True,blank=True)
    status = models.CharField(max_length=512, blank=True, null=True)
    last_status_update = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.name)

    @property
    def authors_by_year(self):
        return Author.objects.filter(name__researcher_id=self.id).order_by('-paper__pubdate')
    @property
    def names(self):
        return Name.objects.filter(author__researcher=self)
    @property
    def aka(self):
        return self.names[1:]
    def update_variants(self):
        """
        Sets the variants of this name to the candidates returned by variants_queryset
        """
        self.name_variants.clear()
        last = self.name.last
        for name in Name.objects.filter(last__iexact=last):
            if match_names((name.first,name.last),(self.name.first,self.name.last)):
                self.name_variants.add(name)
                if not name.is_known:
                    name.is_known = True
                    name.save(update_fields=['is_known'])

    stats = models.ForeignKey(AccessStatistics, null=True)
    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(author__researcher=self).distinct())

    @classmethod
    def create_from_scratch(cls, first, last, dept, email, role, homepage):
        name, created = Name.objects.get_or_create(full=iunaccent(first+' '+last),
                defaults={'first':first, 'last':last})
        if not created and cls.objects.filter(name=name).count() > 0:
            # we forbid the creation of two researchers with the same name,
            # although our model would support it (TODO ?)
            raise ValueError

        researcher = Researcher(
                department=dept,
                email=email,
                role=role,
                homepage=homepage,
                name=name)
        researcher.save()
        researcher.update_variants()
        researcher.update_stats()
        return researcher


MAX_NAME_LENGTH = 256
class Name(models.Model):
    first = models.CharField(max_length=MAX_NAME_LENGTH)
    last = models.CharField(max_length=MAX_NAME_LENGTH)
    full = models.CharField(max_length=MAX_NAME_LENGTH*2+1, db_index=True)
    is_known = models.BooleanField(default=False)

    unique_together = ('first','last')
    
    class Meta:
        ordering = ['last','first']

    @classmethod
    def create(cls, first, last):
        """
        Creates an instance of the Name object without saving it.
        Useful for name lookups where we are not sure we want to
        keep the name in the model.
        """
        first = first[:MAX_NAME_LENGTH]
        last = last[:MAX_NAME_LENGTH]
        full = iunaccent(first+' '+last)
        return cls(first=first,last=last,full=full)
    @classmethod
    def get_or_create(cls, first, last):
        """
        Replacement for the regular get_or_create, so that the full
        name is built based on first and last
        """
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
        self.variant_of.clear()
        for researcher in self.variants_queryset():
            if match_names((researcher.name.first,researcher.name.last), (self.first,self.last)):
                researcher.name_variants.add(self)

    def update_is_known(self):
        """
        A name is considered as known when it belongs to a name variants group of a researcher
        """
        new_value = self.variant_of.count() > 0
        if new_value != self.is_known:
            self.is_known = new_value
            self.save(update_fields=['is_known'])

    @classmethod
    def lookup_name(cls, author_name):
        if author_name == None:
            return
        first_name = author_name[0][:MAX_NAME_LENGTH]
        last_name = author_name[1][:MAX_NAME_LENGTH]

        # First, check if the name itself is known
        # (we do not take the first/last separation into account
        # here because the exact match is already a quite strong
        # condition)
        full_name = first_name+' '+last_name
        full_name = full_name.strip()
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

        saved = False
        for r in similar_researchers:
            if match_names((r.name.first,r.name.last), (first_name,last_name)):
                if not saved:
                    saved = True
                    name.is_known = True
                    name.save()
                r.name_variants.add(name)

   
        # Other approach that adds *many* names
        #
        #similar_names = cls.objects.filter(last__iexact=last_name, is_known=True)
        #for sim in similar_names:
        #    if match_names((sim.first,sim.last),(first_name,last_name)):
        #        name.is_known = True
        #        name.save()
        #        for researcher in sim.variant_of.all():
        #            researcher.name_variants.add(name)

        return name

    # Used to save unsaved names after lookup
    def save_if_not_saved(self):
        if not self.pk:
            # the is_known field should already be up to date as it is computed in the lookup
            self.save()
            self.update_variants()

    def __unicode__(self):
        return '%s %s' % (self.first,self.last)

    def first_letter(self):
        return self.last[0]

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
        return self.pubdate.year

    @property
    def prioritary_oai_records(self):
        return self.sorted_oai_records.filter(priority__gt=0)

    @property
    def sorted_oai_records(self):
        return self.oairecord_set.order_by('-priority')

    @property
    def sorted_authors(self):
        return self.author_set.order_by('id').select_related('name')

    def author_count(self):
        if self.cached_author_count == None:
            self.cached_author_count = self.author_set.count()
        return self.cached_author_count

    def has_many_authors(self):
        return self.author_count() > 15

    def interesting_authors(self):
        lst = (list(self.sorted_authors.filter(name__is_known=True))+list(
            self.sorted_authors.filter(name__is_known=False))[:3])[:15]
        self.nb_remaining_authors = self.author_count() - len(lst)
        return lst

    def displayed_authors(self):
        if self.has_many_authors():
            return self.interesting_authors()
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
                            '-source__oa', 'source__priority').select_related('source')
            self.pdf_url = None
            for m in matches:
                if not self.pdf_url:
                    self.pdf_url = m.pdf_url
                if m.source.oa:
                    self.oa_status = 'OA'

                if m.pubtype in PAPER_TYPE_PREFERENCE:
                    new_idx = PAPER_TYPE_PREFERENCE.index(m.pubtype)
                    type_idx = min(new_idx, type_idx)

        self.doctype = PAPER_TYPE_PREFERENCE[type_idx]
        self.save()
        self.invalidate_cache()

    def publications_with_unique_publisher(self):
        seen_publishers = set()
        for publication in self.publication_set.all():
            if publication.publisher_id and publication.publisher_id not in seen_publishers:
                seen_publishers.add(publication.publisher_id)
                yield publication

    def plain_fingerprint(self):
        """
        Debugging function to display the plain fingerprint
        """
        authors = [(a.name.first,a.name.last) for a in self.author_set.all().select_related('name')]
        return create_paper_plain_fingerprint(self.title, authors)

    def new_fingerprint(self):
        buf = self.plain_fingerprint()
        m = hashlib.md5()
        m.update(buf)
        return m.hexdigest()

    def invalidate_cache(self):
        for rpk in [a.researcher_id for a in self.author_set.filter(researcher_id__isnull=False)]+[None]:
            for with_buttons in [False,True]:
                key = make_template_fragment_key('publiListItem', [self.pk, rpk, with_buttons])
                cache.delete(key)

    # Merge paper into self
    def merge(self, paper):
        # TODO What if the authors are not the same?
        # We should merge the list of authors, so that the order is preserved

        # TODO merge author relations

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




# Researcher / Paper binary relation
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    name = models.ForeignKey(Name)
    cluster = models.ForeignKey('Author', blank=True, null=True, related_name='clusterrel')
    num_children = models.IntegerField(default=1)
    cluster_relevance = models.FloatField(default=0) # TODO change this default to a negative value
    similar = models.ForeignKey('Author', blank=True, null=True, related_name='similarrel')
    researcher = models.ForeignKey(Researcher, blank=True, null=True, on_delete=models.SET_NULL)

    affiliation = models.CharField(max_length=512, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)
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

# Publisher associated with a journal
class Publisher(models.Model):
    romeo_id = models.CharField(max_length=64)
    name = models.CharField(max_length=256, db_index=True)
    alias = models.CharField(max_length=256,null=True,blank=True)
    url = models.URLField(null=True,blank=True)
    preprint = models.CharField(max_length=32, choices=POLICY_CHOICES, default='unknown')
    postprint = models.CharField(max_length=32, choices=POLICY_CHOICES, default='unknown')
    pdfversion = models.CharField(max_length=32, choices=POLICY_CHOICES, default='unknown')
    oa_status = models.CharField(max_length=32, choices=OA_STATUS_CHOICES, default='UNK')

    stats = models.ForeignKey(AccessStatistics, null=True)

    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(publication__publisher=self).distinct())
    def __unicode__(self):
        if not self.alias:
            return self.name
        else:
            return self.name+' ('+self.alias+')'
    @property
    def publi_count(self):
        # TODO ensure that the papers are not only visible,
        # but also assigned to a researcher
        if self.stats:
            return self.stats.num_tot
        return 0

    @property
    def sorted_journals(self):
        return self.journal_set.all().select_related('stats').filter(stats__num_tot__gt=0).order_by('-stats__num_tot')
    @property
    def preprint_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='preprint')
    @property
    def postprint_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='postprint')
    @property
    def pdfversion_conditions(self):
        return self.publisherrestrictiondetail_set.filter(applies_to='pdfversion')
    def change_oa_status(self, new_oa_status):
        if self.oa_status == new_oa_status:
            return
        self.oa_status = new_oa_status
        self.save()
        papers = Paper.objects.filter(publication__publisher=self.pk)
        for p in papers:
            p.update_availability()
            p.invalidate_cache()

# Journal data retrieved from RoMEO
class Journal(models.Model):
    title = models.CharField(max_length=256, db_index=True)
    last_updated = models.DateTimeField(auto_now=True)
    issn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    publisher = models.ForeignKey(Publisher)

    stats = models.ForeignKey(AccessStatistics, null=True)
    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        self.stats.update(Paper.objects.filter(publication__journal=self).distinct())

    def __unicode__(self):
        return self.title
    class Meta:
        ordering = ['title']

class PublisherCondition(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=1024)
    def __unicode__(self):
        return self.text

class PublisherCopyrightLink(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    url = models.URLField()
    def __unicode__(self):
        return self.text

class PublisherRestrictionDetail(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    applies_to = models.CharField(max_length=32)
    def __unicode__(self):
        return self.text

class Disambiguation(models.Model):
    publications = models.ManyToManyField('Publication')
    title = models.CharField(max_length=512)
    issn = models.CharField(max_length=128)
    unique_together = ('title', 'issn')

class DisambiguationChoice(models.Model):
    about = models.ForeignKey(Disambiguation)
    title = models.CharField(max_length=512)
    issn = models.CharField(max_length=128)

# Counts the number of times a given publisher string has
# been associated with a model publisher
class AliasPublisher(models.Model):
    publisher = models.ForeignKey(Publisher)
    name = models.CharField(max_length=512)
    count = models.IntegerField(default=0)
    unique_together = ('name','publisher')

    def __unicode__(self):
        return self.name + ' --'+str(self.count)+'--> '+self.publisher.name
    @classmethod
    def increment(cls, name, publisher):
        # TODO it would be more efficient with an update, but it does not really work
        if not name:
            return
        alias, created = cls.objects.get_or_create(name=name, publisher=publisher)
        alias.count += 1
        alias.save()

# Publication of these papers (in journals or conference proceedings)
class Publication(models.Model):
    # TODO prepare this model for user input (allow for other URLs than DOIs)
    paper = models.ForeignKey(Paper)
    pubtype = models.CharField(max_length=64)

    title = models.CharField(max_length=512) # this is actually the *journal* title
    journal = models.ForeignKey(Journal, blank=True, null=True)

    publisher = models.ForeignKey(Publisher, blank=True, null=True)
    publisher_name = models.CharField(max_length=512, blank=True, null=True)

    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    pubdate = models.DateField(blank=True, null=True)

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
    identifier = models.CharField(max_length=300)
    name = models.CharField(max_length=100)
    oa = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)
    default_pubtype = models.CharField(max_length=128)

    # Fetching properties
    last_status_update = models.DateTimeField(auto_now=True)
    def __unicode__(self):
        return self.name

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


