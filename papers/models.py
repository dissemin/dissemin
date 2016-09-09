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

from datetime import datetime
from datetime import timedelta
import re
import hashlib
from urllib import quote  # for the Google Scholar and CORE link
from urllib import urlencode
from statistics.models import AccessStatistics
from statistics.models import combined_status_for_instance
from statistics.models import STATUS_CHOICES_HELPTEXT

from celery.result import AsyncResult
from dissemin.settings import POSSIBLE_LANGUAGE_CODES
from dissemin.settings import PROFILE_REFRESH_ON_LOGIN
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import DataError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from papers.baremodels import BareAuthor
from papers.baremodels import BareName
from papers.baremodels import BareOaiRecord
from papers.baremodels import MAX_NAME_LENGTH
from papers.categories import PAPER_TYPE_CHOICES
from papers.categories import PAPER_TYPE_PREFERENCE
from papers.oaisource import OaiSource
from papers.doi import to_doi
from papers.errors import MetadataSourceException
from papers.name import name_similarity
from papers.name import unify_name_lists
from papers.orcid import OrcidProfile
from papers.utils import affiliation_is_greater
from papers.utils import validate_orcid
from papers.utils import sanitize_html
from papers.utils import maybe_recapitalize_title
from papers.utils import canonicalize_url
from papers.utils import datetime_to_date
from papers.utils import remove_diacritics
from papers.utils import remove_nones
from papers.fingerprint import create_paper_plain_fingerprint
from publishers.models import Journal
from publishers.models import Publisher
from publishers.models import DummyPublisher
from publishers.models import OA_STATUS_CHOICES
from publishers.models import OA_STATUS_PREFERENCE
from solo.models import SingletonModel

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
        self.stats.clear()
        for d in self.sorted_departments:
            self.stats.add(d.stats)
        self.stats.save()

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
        return [(unicode(self), self.url)]


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
        self.stats.clear()
        for r in self.sorted_researchers:
            self.stats.add(r.stats)
        self.stats.save()

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
        return self.institution.breadcrumbs()+[(unicode(self), self.url)]


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
        unique_together = (('name', 'researcher'),)


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
    email = models.EmailField(blank=True, null=True)
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
    current_task = models.CharField(
        max_length=64, choices=HARVESTER_TASK_CHOICES, null=True, blank=True)

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
        return reverse('researcher', kwargs={'researcher': self.pk, 'slug': self.slug})

    @property
    def papers(self):
        """
        :py:class:`Paper` objects for this researcher,
        sorted by decreasing publication date
        """
        return Paper.objects.filter(
                authors_list__contains=[{'researcher_id': self.id}]
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

        for name in self.variants_queryset():
            sim = name_similarity((name.first, name.last),
                                  (self.name.first, self.name.last))
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
        NameVariant.objects.get_or_create(
                name=name, researcher=self, defaults={'confidence': confidence})
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
        from backend.tasks import fetch_everything_for_researcher
        self.harvester = fetch_everything_for_researcher.delay(pk=self.id).id
        self.current_task = 'init'
        self.save(update_fields=['harvester', 'current_task'])

    def fetch_everything_if_outdated(self):
        if self.last_harvest is None or timezone.now() - self.last_harvest > PROFILE_REFRESH_ON_LOGIN:
            self.fetch_everything()

    def init_from_orcid(self):
        from backend.tasks import init_profile_from_orcid
        self.harvester = init_profile_from_orcid(pk=self.id).id
        self.current_task = 'init'
        self.save(update_fields=['harvester', 'current_task'])

    @classmethod
    def get_or_create_by_orcid(cls, orcid, profile=None, user=None):
        """
        Creates (or returns an existing) researcher from its ORCID id.

        :param profile: an :class:`OrcidProfile` object if it has already been fetched
                        from the API (otherwise we will fetch it ourselves)
        :param user: an user to associate with the profile.
        :returns: a :class:`Researcher` if everything went well, raises MetadataSourceException otherwise
        """
        researcher = None
        if orcid is None:
            raise MetadataSourceException('Invalid ORCID id')
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
            researcher = Researcher.create_by_name(name[0], name[1], orcid=orcid,
                                                   user=user, homepage=homepage, email=email)

            # Ensure that extra info is added.
            save = False
            for kw, val in [('homepage', homepage), ('orcid', orcid), ('email', email)]:
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
            researcher, created = Researcher.objects.get_or_create(
                name=name, orcid=orcid, defaults=kwargs)
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
        last = [(unicode(self), self.url)]
        if not self.department:
            return last
        else:
            return self.department.breadcrumbs()+last

    @cached_property
    def latest_paper(self):
        """
        Returns the latest paper authored by this researcher, if any.
        """
        lst = list(self.papers[:1])
        if lst:
            return lst[0]

    def affiliation_form(self):
        """
        Returns a form to change the affiliation of this researcher
        """
        from papers.forms import ResearcherDepartmentForm
        data = {'pk': self.id,
                'department': self.department_id}
        return ResearcherDepartmentForm(initial=data)


class Name(models.Model, BareName):
    first = models.CharField(max_length=MAX_NAME_LENGTH)
    last = models.CharField(max_length=MAX_NAME_LENGTH)
    full = models.CharField(max_length=MAX_NAME_LENGTH*2+1, db_index=True)
    best_confidence = models.FloatField(default=0.)

    class Meta:
        unique_together = ('first', 'last')
        ordering = ['last', 'first']

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
                                         defaults={'first': n.first, 'last': n.last})

    def variants_queryset(self):
        """
        Returns the queryset of should-be variants.
        WARNING: This is to be used on a name that is already associated with a researcher.
        """
        # TODO this could be refined (icontains?)
        return Researcher.objects.filter(name__last__iexact=self.last)

    def update_variants(self):
        """
        Sets the variants of this name to the candidates returned by variants_queryset
        """
        for researcher in self.variants_queryset():
            sim = name_similarity(
                (researcher.name.first, researcher.name.last), (self.first, self.last))
            if sim > 0:
                old_sim = self.best_confidence
                self.best_confidence = sim
                if self.pk is None or old_sim < sim:
                    self.save()
                NameVariant.objects.get_or_create(name=self, researcher=researcher,
                                                  defaults={'confidence': sim})

    def update_best_confidence(self):
        """
        A name is considered as known when it belongs to a name variants group of a researcher
        """
        new_value = max([0.]+[d['confidence']
                              for d in self.namevariant_set.all().values('confidence')])
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
            return bare_name  # not so bare…
        return cls.lookup_name((bare_name.first, bare_name.last))

    def save_if_not_saved(self):
        """
        Used to save unsaved names after lookup
        """
        if self.pk is None:
            # the best_confidence field should already be up to date as it is
            # computed in the lookup
            self.save()
            self.update_variants()

    @property
    def object_id(self):
        """Criteria to use in the search view to filter on this name"""
        return "name=%d" % self.pk


# Papers matching one or more researchers
class Paper(models.Model):
    title = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=64, unique=True)
    date_last_ask = models.DateField(null=True)  # TODO remove (unused)

    #: Approximate publication date.
    #: For instance if we only know it is in 2014 we'll put 2014-01-01
    pubdate = models.DateField()

    #: Full list of authors for this paper
    authors_list = JSONField(default=list)

    #: Relation to Researcher: all researchers that appear in
    #: authors_list (not all authors are researchers because not all
    #: authors have profiles on dissemin)
    researchers = models.ManyToManyField(Researcher)

    #: List of all identifiers of this paper.
    #: This includes the fingerprint, DOIs and OAI ids.
    #: All of these values should be unique to a Paper instance
    #: (although this is not enforced in the database yet).
    identifiers = ArrayField(models.CharField(max_length=512), null=True, blank=True)

    #: List of all records of this paper, stored as a JSON object
    #: Each record is a dict with all the record information
    records_list = JSONField(default=list)

    last_modified = models.DateTimeField(auto_now=True, db_index=True)
    visible = models.BooleanField(default=True)
    last_annotation = models.CharField(max_length=32, null=True,
            blank=True) # TODO remove (unused)

    doctype = models.CharField(
        max_length=64, null=True, blank=True, choices=PAPER_TYPE_CHOICES)

    # The two following fields need to be updated after the relevant changes
    # using the methods below.
    oa_status = models.CharField(
        max_length=32, null=True, blank=True, default='UNK')
    pdf_url = models.URLField(max_length=2048, null=True, blank=True)

    # Task id of the current task updating the metadata of this article (if any)
    task = models.CharField(max_length=512, null=True, blank=True)

    # Value above which we consider a paper to have too many authors to be
    # displayed. See Paper.has_many_authors
    MAX_DISPLAYED_AUTHORS = 15

    # Creation

    def __init__(self, *args, **kwargs):
        super(Paper, self).__init__(*args, **kwargs)
        #! If there are lots of authors, how many are we hiding?
        self.nb_remaining_authors = None

    @classmethod
    def create(cls, title, author_names, pubdate, visible=True,
               affiliations=None, orcids=None):
        """
        Creates a paper (not saved to the database).

        :param title: The title of the paper (as a string). If it is too long for the database,
                      ValueError is raised.
        :param author_names: The ordered list of author names, as Name objects.
        :param pubdate: The publication date, as a python date object
        :param visible: The visibility of the paper if it is created. If another paper
                    exists, the visibility will be set to the maximum of the two possible
                    visibilities.
        :param affiliations: A list of (possibly None) affiliations for the authors. It has to
                    have the same length as the list of author names.
        :param orcids: same as affiliations, but for ORCID ids.
        """
        if not title or not author_names or not pubdate:
            raise ValueError(
                "A title, pubdate and authors have to be provided to create a paper.")

        if affiliations is not None and len(author_names) != len(affiliations):
            raise ValueError(
                "The number of affiliations and authors have to be equal.")
        if orcids is not None and len(author_names) != len(orcids):
            raise ValueError(
                "The number of ORCIDs (or Nones) and authors have to be equal.")
        if type(visible) != bool:
            raise ValueError("Invalid paper visibility: %s" % unicode(visible))

        title = sanitize_html(title)
        title = maybe_recapitalize_title(title)

        p = cls()
        p.title = title
        p.pubdate = pubdate  # pubdate will be checked in fingerprint computation
        p.visible = visible
        for idx, n in enumerate(author_names):
            a = BareAuthor()
            a.name = n
            if affiliations is not None:
                a.affiliation = affiliations[idx]
            if orcids is not None:
                orcid = validate_orcid(orcids[idx])
                if orcid:
                    a.orcid = orcid
            p.add_author(a, position=idx)

        p.fingerprint = p.new_fingerprint()
        p.update_identifiers()

        return p

    @property
    def slug(self):
        return slugify(self.title)

    ### Submodels ###

    @property
    def authors(self):
        """
        The author sorted as they should appear.
        """
        return map(BareAuthor.deserialize, self.authors_list)

    @property
    def oairecords(self):
        """
        The list of OAI records associated with this paper. It can
        be arbitrary iterables of subclasses of :class:`BareOaiRecord`.
        """
        return map(BareOaiRecord.deserialize, self.records_list)

    def add_oairecord(self, oairecord):
        """
        Adds a new OAI record to the paper

        :returns: the :class:`BareOaiRecord` that was added (it can differ in subclasses)
        """
        oairecord.check_mandatory_fields()
        oairecord.cleanup_description()
        
        # Search for an existing record that would match
        # the URLs we are trying to add
        matching_idx = None
        match = None
        new_short_splash = canonicalize_url(oairecord.splash_url)
        new_short_pdf = canonicalize_url(oairecord.pdf_url)
        for idx, rec in enumerate(self.oairecords):
            short_splash = canonicalize_url(rec.splash_url)
            short_pdf = canonicalize_url(rec.pdf_url)
            if (rec.identifier == oairecord.identifier or
                new_short_splash == short_splash or
                (short_pdf and new_short_pdf == short_pdf)):
                matching_idx = idx
                match = rec
                break

        if matching_idx is None:
            self.records_list.append(oairecord.serialize())
        else:
            # Update the matching record with the newer values
            # (only if needed)
            splash_url = oairecord.splash_url
            pdf_url = oairecord.pdf_url            
            source = oairecord.source

            if (pdf_url != None and (match.pdf_url == None or
                (match.pdf_url != pdf_url and match.priority <
                            source.priority))):
                match.source = source
                match.priority = source.priority
                match.pdf_url = pdf_url
                match.splash_url = splash_url

            def update_field_conditionally(field):
                new_val = getattr(oairecord, field, '')
                if new_val and (len(getattr(match, field) or '') < len(new_val)):
                    setattr(match, field, new_val)

            update_field_conditionally('contributors')
            update_field_conditionally('keywords')
            update_field_conditionally('description')
            update_field_conditionally('doi')

            new_pubtype = oairecord.pubtype
            if new_pubtype in PAPER_TYPE_PREFERENCE:
                idx = PAPER_TYPE_PREFERENCE.index(new_pubtype)
                old_idx = len(PAPER_TYPE_PREFERENCE)-1
                if match.pubtype in PAPER_TYPE_PREFERENCE:
                    old_idx = PAPER_TYPE_PREFERENCE.index(match.pubtype)
                if idx < old_idx:
                    changed = True
                    match.pubtype = PAPER_TYPE_PREFERENCE[idx]

            self.records_list[matching_idx] = oairecord.serialize()

        # update the publication date
        self.pubdate = datetime_to_date(self.pubdate)
        if oairecord.pubdate:
            new_pubdate = datetime_to_date(oairecord.pubdate)
            if new_pubdate > self.pubdate:
                self.pubdate = new_pubdate

        # update identifiers
        self.update_identifiers()

    def remove_oairecord(self, identifier):
        """
        Remove the OAI record that matches a particular identifier.
        If there is no such OAI record, does not do anything.
        """
        new_records = filter(lambda r: r['identifier'] != identifier,
                    self.records_list)
        self.records_list = new_records
        self.update_identifiers()

    @property
    def year(self):
        """
        Year of publication of the paper.
        """
        return self.pubdate.year

    # OAI records -----------------

    @cached_property
    def sorted_oai_records(self):
        """
        OAI records sorted by decreasing order of priority
        (lower priority means poorer overall quality of the source).
        """
        # Ordered in Python because the list of records is typically quite
        # small (less than 10 items)
        return sorted(self.oairecords, key=lambda r: -r.priority)

    @cached_property
    def prioritary_oai_records(self):
        """
        OAI records from custom sources we trust (positive priority)
        """
        # Filtered in Python because the list of records is typically quite
        # small (less than 10 items)
        return filter(lambda r: r.priority > 0, self.sorted_oai_records)

    @property
    def unique_prioritary_oai_records(self):
        """
        OAI records from sources we trust, with unique source.
        """
        seen_sources = set()
        for record in self.prioritary_oai_records:
            if record.source_id not in seen_sources:
                seen_sources.add(record.source_id)
                yield record

    def update_identifiers(self):
        """
        Refreshes the list of identifiers for this paper
        """
        identifiers = set([self.fingerprint])
        for r in self.oairecords:
            identifiers.add(r.identifier)
            if r.doi:
                identifiers.add(r.doi)
        self.identifiers = list(identifiers)

    # Authors ------------------------

    def author_names(self):
        """
        The list of Name instances of the authors
        """
        return [a.name for a in self.authors]

    def affiliations(self):
        """
        The list of affiliations of all authors
        """
        return [a.affiliation for a in self.authors]

    def orcids(self):
        """
        The list of ORCIDs of all authors
        """
        return [a.orcid for a in self.authors]

    def bare_author_names(self):
        """
        The list of name pairs (first,last) of the authors
        """
        return [(name.first, name.last) for name in self.author_names()]

    @property
    def author_count(self):
        """
        Number of authors.
        """
        return len(self.authors)

    @property
    def has_many_authors(self):
        """
        When the paper has more than some arbitrary number of authors.
        """
        return self.author_count > self.MAX_DISPLAYED_AUTHORS

    @cached_property
    def interesting_authors(self):
        """
        The list of authors to display when the complete list is too long.
        """
        # TODO: Better selection
        lst = self.authors[:self.MAX_DISPLAYED_AUTHORS]
        self.nb_remaining_authors = self.author_count - len(lst)
        return lst

    def displayed_authors(self):
        """
        Returns the full list of authors if there are not too many of them,
        otherwise returns only the interesting_authors()
        """
        if self.has_many_authors:
            return self.interesting_authors
        else:
            return self.authors

    def check_authors(self):
        """
        Check the sanity of authors
        (for now, only that the list is non-empty)
        """
        if not self.authors:
            raise ValueError("Empty authors list")
        # TODO more checks here?

    # Publications ---------------------------------------------

    @property
    def publications(self):
        """
        The OAI records with publication metadata (i.e. journal title and
        publisher name).
        These records can potentially be associated with publisher policies.
        """
        res = []
        # we don't yield because some functions actually do len( ) on the
        # output of this method…
        for r in self.oairecords:
            if r.has_publication_metadata():
                res.append(r)
        return res

    def first_publications(self):
        """
        The list of the 3 first OAI records with publication metadata
        associated with this paper (in most cases, that should return *all*
        such records, but in some nasty cases many publications end up
        merged, and it is not very elegant to show all of them
        to the users).
        """
        return list(self.publications)[:3]

    def publications_with_unique_publisher(self):
        """
        Iterable of publications where subsequent publications with
        the same publisher are removed.
        """
        seen_publishers = set()
        for publication in self.publications:
            if publication.publisher_id and publication.publisher_id not in seen_publishers:
                seen_publishers.add(publication.publisher_id)
                yield publication
            elif publication.publisher_name not in seen_publishers:
                seen_publishers.add(publication.publisher_name)
                yield publication

    def publisher(self):
        """
        Returns the first publisher we can find for this paper, otherwise
        a :class:`DummyPublisher`
        """
        for publication in self.publications:
            return publication.publisher_or_default()
        return DummyPublisher()

    # Fingerprint -----------------------------------------------
    def plain_fingerprint(self, verbose=False):
        """
        Debugging function to display the plain fingerprint
        """
        fp = create_paper_plain_fingerprint(
            self.title, self.bare_author_names(), self.year)
        if verbose:
            print fp
        return fp

    def new_fingerprint(self, verbose=False):
        """
        The fingerprint of the paper, taking into account the changes
        that may have occured since the last computation of the fingerprint.
        This does not update the `fingerprint` field, just computes its candidate value.
        """
        buf = self.plain_fingerprint(verbose)
        m = hashlib.md5()
        m.update(buf)
        return m.hexdigest()

    # Abstract -------------------------------------------------
    @cached_property
    def abstract(self):
        best_abstract = ''
        for rec in self.oairecords:
            if rec.description and len(rec.description) > len(best_abstract):
                best_abstract = rec.description
        return best_abstract

    # Updates ---------------------------------------------------
    def update_availability(self):
        """
        Updates the :class:`Paper`'s own `pdf_url` field
        based on its sources (:class:`BareOaiRecord`).

        This uses a non-trivial logic, hence it is useful to keep this result cached
        in the database row.
        """
        records = self.oairecords
        records = sorted(records, key=(lambda r: -r.priority))

        self.pdf_url = None
        oa_idx = len(OA_STATUS_PREFERENCE)-1
        type_idx = len(PAPER_TYPE_PREFERENCE)-1
        source_found = False

        if self.doctype in PAPER_TYPE_PREFERENCE:
            type_idx = PAPER_TYPE_PREFERENCE.index(self.doctype)

        for rec in records:
            if rec.has_publication_metadata():
                # OA status
                cur_status = rec.oa_status()
                try:
                    idx = OA_STATUS_PREFERENCE.index(cur_status)
                except ValueError:
                    idx = len(OA_STATUS_PREFERENCE)
                oa_idx = min(idx, oa_idx)
                if OA_STATUS_CHOICES[oa_idx][0] == 'OA':
                    self.pdf_url = rec.pdf_url or rec.splash_url
            else:
                if not self.pdf_url and rec.pdf_url:
                    self.pdf_url = rec.pdf_url

            # Pub type
            cur_type = rec.pubtype
            try:
                idx = PAPER_TYPE_PREFERENCE.index(cur_type)
            except ValueError:
                idx = len(PAPER_TYPE_PREFERENCE)
            type_idx = min(idx, type_idx)

            source_found = True

        self.oa_status = OA_STATUS_CHOICES[oa_idx][0]

        # If this paper is not associated with any source, do not display it
        # This happens when creating the associated OaiRecord
        # failed due to some missing information.
        if not source_found:
            self.visible = False

        self.doctype = PAPER_TYPE_PREFERENCE[type_idx]
        self.invalidate_cache()

    def update_visible(self):
        """
        Updates the visibility of the paper. Only papers with at least
        one source should be visible.
        """
        old_visible = self.visible
        self.visible = not self.is_orphan()
        if self.visible != old_visible:
            self.save(update_fields=['visible'])

    # Other representations ------------------------------------------
    def __unicode__(self):
        """
        Title of the paper
        """
        return self.title

    def json(self):
        """
        JSON representation of the paper, for dataset dumping purposes
        """
        return remove_nones({
            'title': self.title,
            'type': self.doctype,
            'date': self.pubdate.isoformat(),
            'authors': [a.json() for a in self.authors],
            'records': [r.json() for r in self.oairecords],
            'pdf_url': self.pdf_url,
            'classification': self.oa_status,
            })

    def google_scholar_link(self):
        """
        Link to search for the paper in Google Scholar
        """
        return 'http://scholar.google.com/scholar?'+urlencode({'q': remove_diacritics(self.title)})

    def is_orphan(self):
        """
        When no OAI record is associated with this paper.
        """
        return (len(self.oairecords) == 0)

    def citation(self):
        """
        A short citation-like representation of the paper. E.g. Joyal and Street, 1992
        """
        result = ''
        if self.author_count == 1:
            result = self.authors[0].name.last
        elif self.author_count == 2:
            result = "%s and %s" % (
                self.authors[0].name.last,
                self.authors[1].name.last)
        else:
            result = "%s et al." % (
                self.authors[0].name.last)
        result += ', %d' % self.year
        return result


    ### Relations to other models  ###

    def add_author(self, author, position=None):
        """
        Add an author at the end of the authors list by default
        or at the specified position.

        The change is not commited to the database
        (you need to call save() afterwards).

        :param position: add the author at that index.
        """
        author_serialized = author.serialize()
        if position is None:
            position = len(self.authors_list)
        if not (position >= 0 and position <= len(self.authors_list)):
            raise ValueError("Invalid author position '%s' of %d" %
                                (str(position), len(self.authors_list)))
        self.authors_list.insert(position, author_serialized)
        if author.researcher_id:
            self.researchers.add(author.researcher_id)
        return author

    def set_researcher(self, position, researcher_id):
        """
        Sets the researcher_id for the author at the given position
        (0-indexed)
        """
        if position < 0 or position > len(self.authors_list):
            raise ValueError('Invalid position provided')
        self.authors_list[position]['researcher_id'] = researcher_id
        self.save(update_fields=['authors_list'])
        self.researchers.add(researcher_id)

    ### Paper creation ###

    @classmethod
    def get_or_create(cls, title, author_names, pubdate, visible=True, affiliations=None):
        """
        Creates an (initially) bare paper and saves it to the database.

        :returns: the corresponding :class:`Paper` instance.
        """
        p = Paper.create(title, author_names, pubdate,
                             visible, affiliations)
        p.save()
        return p

    @classmethod
    def find_by_fingerprint(cls, fp):
        return Paper.objects.filter(fingerprint__exact=fp)

    @classmethod
    def find_by_identifiers(cls, identifiers):
        """
        :returns: a QuerySet of Paper instances whose identifiers
        overlap with the given identifiers list
        """
        # we could use
        # Paper.objects.filter(identifiers__overlap=identifiers)
        # but this adds a LIMIT on the results and for some reason
        # postgresql does not get query planning right in that case
        # (it does not use the index) so we use a custom SQL query here.
        # 
        # for more info, see
        # https://dba.stackexchange.com/questions/146679/forcing-postgres-to-use-a-gin-index-on-a-varchar
        return Paper.objects.raw(
            "SELECT * FROM papers_paper WHERE identifiers && %s::varchar(512)[]",
                [identifiers])

    def save(self, **kwargs):
        """
        Saves a paper to the database if it is not already present.
        """
        if self.id:
            super(Paper, self).save(**kwargs)
            return

        try:
            # Look up the paper in the database
            self.update_identifiers()
            matches = list(Paper.find_by_identifiers(self.identifiers))
            
            # We now have a list of papers whose identifiers overlap with
            # the identifiers of the papers we are trying to add.

            if not matches:
                # If there are no matches, that's very simple: we just INSERT
                # the new paper in the database.
                self.update_availability()
                super(Paper, self).save()

            else:
                # Otherwise, one or more matching papers were found.

                # For instance, we might already have a paper in the database
                # with the same DOI, and another paper with the same
                # fingerprint (but these two are not equal yet, because the
                # DOI metadata might yield another fingerprint).

                # All these papers need to be merged into the same object.
                # We choose an arbitrary matching order (because how else
                # can we choose?)
                for i in range(1,len(matches)):
                    matches[0].merge(matches[i])
                
                p = matches[0]
                if self.visible and not p.visible:
                    p.visible = True
                p.update_authors(
                        self.authors,
                        save_now=False)
                for record in self.oairecords:
                    p.add_oairecord(record)
                p.update_availability()
                p.save()

                # set the current instance to p
                self.__dict__.update(p.__dict__)

        except DataError as e:
            raise ValueError(
                'Invalid paper, does not fit in the database schema:\n'+unicode(e))

    ### Other methods, specific to this non-bare subclass ###

    def update_author_stats(self):
        """
        Updates the statistics of all researchers identified for this paper
        """
        for author in self.authors:
            if author.researcher:
                author.researcher.update_stats()

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

    @cached_property
    def is_deposited(self):
        return self.successful_deposits().count() > 0

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
        :returns: the updated version of the paper
        """
        # TODO move task id to paper (or even discard it??)
        if self.task is None:
            from backend.tasks import consolidate_paper
            task = consolidate_paper.delay(pk=self.id)
            self.task = task.id
        else:
            task = AsyncResult(self.task)
        if wait:
            return task.get()

    @classmethod
    def create_by_doi(self, doi):
        """
        Creates a paper given a DOI
        """
        import backend.crossref as crossref
        cr_api = crossref.CrossRefAPI()
        paper = cr_api.create_paper_by_doi(doi)
        return paper

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
                key = make_template_fragment_key(
                    'publiListItem', [self.pk, lang, rpk])
                cache.delete(key)

    def update_authors(self,
                       new_authors,
                       save_now=True):
        """
        Improves the current list of authors by considering a new list of author names.
        Missing authors are added, and names are unified.
        If affiliations are provided, they will replace the old ones if they are
        more informative.

        :param authors: list of BareAuthor instances (the order matters)
        """
        old_authors = list(self.authors)

        # Invalidate cached properties
        if hasattr(self, 'interesting_authors'):
            del self.interesting_authors

        new_author_names = [(a.name.first, a.name.last) for a in
                            new_authors]

        old_names = map(lambda a: (a.name.first, a.name.last), old_authors)
        unified_names = unify_name_lists(old_names, new_author_names)

        unified_authors = []
        for new_name, (old_idx, new_idx) in unified_names:
            if new_name is None:
                # skip duplicate names
                continue

            # Create the author
            author = None
            if old_idx is not None:
                # this name is associated with an existing author
                # so we keep it
                author = old_authors[old_idx]
            else:
                author = new_authors[new_idx]

            # update attributes
            author.name = BareName.create_bare(first=new_name[0],
                                               last=new_name[1])
            if new_idx is not None and affiliation_is_greater(
                    new_authors[new_idx].affiliation,
                    author.affiliation):
                author.affiliation = new_authors[new_idx].affiliation
            if new_idx is not None and new_authors[new_idx].orcid:
                author.orcid = new_authors[new_idx].orcid

            unified_authors.append(author.serialize())
        self.authors_list = unified_authors
        if save_now:
            self.save(update_fields=['authors_list'])

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

        self.visible = paper.visible or self.visible

        for r in paper.oairecords:
            self.add_oairecord(r)
        self.update_authors(paper.authors, save_now=False)

        paper.invalidate_cache()

        # create a copy of the paper to delete,
        # so that the instance we have got as argument
        # is not invalidated
        copied = Paper()
        copied.__dict__.update(paper.__dict__)
        copied.delete()

        paper.id = self.id
        self.update_availability()
        self.save()

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
            result.append((unicode(first_researcher), first_researcher.url))
        result.append((self.citation, self.url))
        return result

    @property
    def url(self):
        return reverse('paper', args=[self.pk, self.slug])


def create_default_stats():
    return AccessStatistics.objects.create().pk

class PaperWorld(SingletonModel):
    """
    A singleton to link to a special instance of AccessStatistics for all papers
    """
    stats = models.ForeignKey(AccessStatistics, default=create_default_stats)

    def update_stats(self):
        """Update the access statistics for all papers"""
        self.stats.update(Paper.objects.filter(visible=True))

    @property
    def object_id(self):
        return ''

    def __unicode__(self):
        return "All papers"

    class Meta:
        verbose_name = "Paper World"
