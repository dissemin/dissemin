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
from papers.utils import nstr, iunaccent, create_paper_plain_fingerprint
from papers.name import match_names
from django.utils.translation import ugettext_lazy as _

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
        return self.researcher_set.select_related('name').order_by('name')

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
    groups = models.ManyToManyField(ResearchGroup,blank=True,null=True)
    
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
        similar_researchers = Researcher.objects.filter(name__last__iexact=last_name).select_related('name')
        if similar_researchers:
            name.is_known = True
            name.save()
        for r in similar_researchers:
            if match_names((r.name.first,r.name.last), (first_name,last_name)):
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

# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64)
    
    # Year of publication, if that means anything (updated when we add OaiRecords or Publications)
    year = models.IntegerField()
    # Approximate publication date.
    # For instance if we only know it is in 2014 we'll put 2014-01-01
    pubdate = models.DateField()

    last_modified = models.DateField(auto_now=True)
    visibility = models.CharField(max_length=32, default='VISIBLE')
    last_annotation = models.CharField(max_length=32, null=True, blank=True)

    def __unicode__(self):
        return self.title

    # The two following fields need to be updated after the relevant changes
    # using the methods below.
    oa_status = models.CharField(max_length=32, null=True, blank=True, default='UNK')
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)

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
        return self.author_set.order_by('id')

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
        for publi in publis:
            cur_status = publi.oa_status()
            try:
                idx = OA_STATUS_PREFERENCE.index(cur_status)
            except ValueError:
                idx = len(OA_STATUS_PREFERENCE)
            oa_idx = min(idx, oa_idx)
            if OA_STATUS_CHOICES[oa_idx][0] == 'OA':
                self.pdf_url = publi.splash_url()
            if oa_idx == 0:
                break
        self.oa_status = OA_STATUS_CHOICES[oa_idx][0]
        if not self.pdf_url:
            matches = OaiRecord.objects.filter(
                    about=self.id,pdf_url__isnull=False).order_by(
                            '-source__oa', 'source__priority')[:1]
            if matches:
                self.pdf_url = matches[0].pdf_url
                if matches[0].source.oa:
                    self.oa_status = 'OA'
        self.save()

    def plain_fingerprint(self):
        """
        Debugging function to display the plain fingerprint
        """
        authors = [(a.name.first,a.name.last) for a in self.author_set.all().select_related('name')]
        return create_paper_plain_fingerprint(self.title, authors)

# Researcher / Paper binary relation
class Author(models.Model):
    paper = models.ForeignKey(Paper)
    name = models.ForeignKey(Name)
    cluster = models.ForeignKey('Author', blank=True, null=True, related_name='clusterrel')
    num_children = models.IntegerField(default=1)
    cluster_relevance = models.FloatField(default=0) # TODO change this default to a negative value
    similar = models.ForeignKey('Author', blank=True, null=True, related_name='similarrel')
    researcher = models.ForeignKey(Researcher, blank=True, null=True, on_delete=models.SET_NULL)
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
    name = models.CharField(max_length=256)
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
        self.stats.update(Paper.objects.filter(publication__journal__publisher=self).distinct())
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
        papers = Paper.objects.filter(publication__journal__publisher=self.pk)
        for p in papers:
            p.update_availability()

# Journal data retrieved from RoMEO
class Journal(models.Model):
    title = models.CharField(max_length=256)
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

# Publication of these papers (in journals or conference proceedings)
class Publication(models.Model):
    # TODO prepare this model for user input (allow for other URLs than DOIs)
    paper = models.ForeignKey(Paper)
    pubtype = models.CharField(max_length=64)
    title = models.CharField(max_length=512) # this is actually the *journal* title
    journal = models.ForeignKey(Journal, blank=True, null=True)
    issue = models.CharField(max_length=64, blank=True, null=True)
    volume = models.CharField(max_length=64, blank=True, null=True)
    pages = models.CharField(max_length=64, blank=True, null=True)
    pubdate = models.DateField(blank=True, null=True)
    publisher = models.CharField(max_length=512, blank=True, null=True)
    doi = models.CharField(max_length=1024, unique=True, blank=True, null=True) # in theory, there is no limit
    def oa_status(self):
        if self.journal:
            return self.journal.publisher.oa_status
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


