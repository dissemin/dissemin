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




from statistics.models import AccessStatistics

from django.apps import apps
from django.urls import reverse
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from search import SearchQuerySet

get_model = apps.get_model


OA_STATUS_CHOICES = (
        ('OA', _('Open access'), _('Freely available from the publisher.')),
        ('OK', _('Allows pre/post prints'),
         _('The publisher sells copies but allows authors to deposit some version of the article in a repository.')),
        ('NOK', _('Forbids pre/post prints'),
         _('The publisher forbids authors to deposit any version of their article online.')),
        ('UNK', _('Policy unclear'), _(
            'For complicated policies, unknown publishers and unpublished documents.')),
   )

POLICY_CHOICES = [('can', _('Allowed')),
                  ('cannot', _('Forbidden')),
                  ('restricted', _('Restricted')),
                  ('unclear', _('Unclear')),
                  ('unknown', _('Unknown'))]


# Minimum number of times we have seen a publisher name
# associated to a publisher to assign this publisher
# to publications where the journal was not found.
# (when this name has only been associated to one publisher)
PUBLISHER_NAME_ASSOCIATION_THRESHOLD = 1000

# Minimum ratio between the most commonly matched journal
# and the second one
PUBLISHER_NAME_ASSOCIATION_FACTOR = 10


OA_STATUS_PREFERENCE = [x[0] for x in OA_STATUS_CHOICES]
OA_STATUS_CHOICES_WITHOUT_HELPTEXT = [(x[0], x[1]) for x in OA_STATUS_CHOICES]


def publishers_breadcrumbs():
    return [(_('Publishers'), reverse('publishers'))]


class DummyPublisher(object):
    """
    Class representing an "unknown" publisher, which means a publisher
    with a name that did not return anything from SHERPA/RoMEO
    """
    pk = None
    preprint = 'unknown'
    postprint = 'unknown'
    pdfversion = 'unknown'
    preprint_conditions = []
    postprint_conditions = []
    pdfversion_conditions = []

    def __init__(self, name=None):
        if name is not None:
            self.name = name
        else:
            self.name = _('Unknown publisher')

    def __str__(self):
        return self.name

# Publisher associated with a journal


class Publisher(models.Model):
    """
    A publisher, as represented by SHERPA/RoMEO.
    See http://www.sherpa.ac.uk/downloads/ for their data model
    """
    romeo_id = models.CharField(max_length=64, db_index=True)
    romeo_parent_id = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=256)
    alias = models.CharField(max_length=256, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    preprint = models.CharField(
        max_length=32, choices=POLICY_CHOICES, default='unknown')
    postprint = models.CharField(
        max_length=32, choices=POLICY_CHOICES, default='unknown')
    pdfversion = models.CharField(
        max_length=32, choices=POLICY_CHOICES, default='unknown')
    oa_status = models.CharField(
        max_length=32, choices=OA_STATUS_CHOICES_WITHOUT_HELPTEXT, default='UNK')
    last_updated = models.DateTimeField(null=True, help_text="last update as reported by RoMEO")

    stats = models.ForeignKey(AccessStatistics, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'papers_publisher'

    @classmethod
    def find(cls, publisher_name):
        """
        Lookup a publisher by name. Return None if could not be found.
        This restricts the search to default policies (those with romeo_parent_id=None)
        """
        try:
            return cls.objects.get(name__iexact=publisher_name, romeo_parent_id__isnull=True)
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            pass

        # Second, let's see if the publisher name has often been associated to a
        # known publisher
        aliases = list(AliasPublisher.objects
            .filter(name=publisher_name, publisher__romeo_parent_id__isnull=True)
            .order_by('-count')[:2])
        if len(aliases) == 1:
            # Only one publisher found. If it has been seen often enough under that name,
            # keep it!
            if aliases[0].count > PUBLISHER_NAME_ASSOCIATION_THRESHOLD:
                return aliases[0].publisher
        elif len(aliases) == 2:
            # More than one publisher found (two aliases returned as we limited to the two first
            # results). Then we need to make sure the first one appears a lot more often than
            # the first
            if (aliases[0].count > PUBLISHER_NAME_ASSOCIATION_THRESHOLD and
                    aliases[0].count > PUBLISHER_NAME_ASSOCIATION_FACTOR*aliases[1].count):
                return aliases[0].publisher


    def classify_oa_status(self):
        """
        Classify the publisher status into one of "OA" (gold open access), "OK" (self-archiving permitted for some version),
        "NOK" (self-archiving not allowed), "UNK" (unknown or unclear policy)..
        """
        status = 'UNK'
        lst = [self.preprint, self.postprint, self.pdfversion]
        if 'can' in lst:
            status = 'OK'
        elif 'cannot' in lst and all([x == 'cannot' or x == 'unknown' for x in lst]):
            status = 'NOK'

        for c in self.publishercondition_set.all():
            if c.text.lower() == 'all titles are open access journals':
                status = 'OA'
            elif 'doaj says it is an open access journal' in c.text.lower():
                status = 'OA'
        return status

    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        from papers.models import Paper
        sqs = SearchQuerySet().models(Paper).filter(publisher=self.id)
        self.stats.update_from_search_queryset(sqs)

    def __str__(self):
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

    @cached_property
    def preprint_conditions(self):
        return list(self.publisherrestrictiondetail_set.filter(applies_to='preprint'))

    @cached_property
    def postprint_conditions(self):
        return list(self.publisherrestrictiondetail_set.filter(applies_to='postprint'))

    @cached_property
    def pdfversion_conditions(self):
        return list(self.publisherrestrictiondetail_set.filter(applies_to='pdfversion'))

    @cached_property
    def conditions(self):
        return list(self.publishercondition_set.all())

    @property
    def has_conditions(self):
        return len(self.conditions) > 0

    @cached_property
    def copyrightlinks(self):
        return list(self.publishercopyrightlink_set.all())

    @property
    def has_copyrightlinks(self):
        return len(self.copyrightlinks) > 0

    def change_oa_status(self, new_oa_status):
        if self.oa_status == new_oa_status:
            return
        self.oa_status = new_oa_status
        self.save()
        papers = get_model('papers', 'Paper').objects.filter(
            oairecord__publisher=self.pk)
        for p in papers:
            p.update_availability()
            p.invalidate_cache()

    def merge(self, other):
        """
        Merge two Publishers together. The other
        one will be deleted and all links to it
        will be updated to point to self.
        """
        from papers.models import OaiRecord
        Journal.objects.filter(publisher_id = other.id).update(publisher_id=self.id)
        OaiRecord.objects.filter(publisher_id = other.id).update(publisher_id=self.id)
        if other.stats:
            other.stats.delete()
        other.delete()

    def breadcrumbs(self):
        result = publishers_breadcrumbs()
        result.append((str(self), self.canonical_url))
        return result

    def json(self):
        """
        A JSON representation of the policy
        """
        return {'preprint': self.preprint,
                'postprint': self.postprint,
                'published': self.pdfversion,
                'romeo_id': self.romeo_id}

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def canonical_url(self):
        return reverse('publisher', kwargs={'pk': self.pk, 'slug': self.slug})

# Journal data retrieved from RoMEO


class Journal(models.Model):
    """
    A journal as represented by SERPA/RoMEO
    """
    title = models.CharField(max_length=256)
    last_updated = models.DateTimeField(auto_now=True)
    issn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    essn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)

    stats = models.ForeignKey(AccessStatistics, null=True, on_delete=models.SET_NULL)

    @classmethod
    def find(cls, issn=None, essn=None, title=None):
        """
        Lookup a journal by title and issn.
        If an issn is provided, it will be used in priority.
        Otherwise we resort to case-insensitive title matching.
        """
        # Look up the journal in the model
        issns = []
        if issn:
            issns.append(issn)
        if essn:
            issns.append(essn)
        # By ISSN
        if issns:
            matches = cls.objects.filter(Q(issn__in=issns) | Q(essn__in=issns))
            if matches:
                return matches[0]

        # By title
        if title:
            matches = cls.objects.filter(title__iexact=title.lower())
            if matches:
                return matches[0]

    def change_publisher(self, new_publisher):
        """
        Changing the publisher of a Journal is a heavy task:
        we need to update all the OaiRecords associated with
        this Journal to map to the new publisher
        """
        oa_status_changed = self.publisher.oa_status != new_publisher.oa_status
        self.publisher = new_publisher
        self.save()
        self.oairecord_set.all().update(publisher = new_publisher)
        if oa_status_changed:
            papers = get_model('papers', 'Paper').objects.filter(
                oairecord__journal=self.pk)
            for p in papers:
                p.update_availability()
                p.invalidate_cache()

    def update_stats(self):
        if not self.stats:
            self.stats = AccessStatistics.objects.create()
            self.save()
        from papers.models import Paper
        sqs = SearchQuerySet().models(Paper).filter(journal=self.id)
        self.stats.update_from_search_queryset(sqs)

    def breadcrumbs(self):
        return self.publisher.breadcrumbs()+[(str(self), '')]

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        db_table = 'papers_journal'


class PublisherCondition(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'papers_publishercondition'


class PublisherCopyrightLink(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    text = models.TextField()
    url = models.URLField(max_length=1024)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'papers_publishercopyrightlink'


class PublisherRestrictionDetail(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    text = models.TextField()
    applies_to = models.CharField(max_length=32)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'papers_publisherrestrictiondetail'

# Counts the number of times a given publisher string has
# been associated with a model publisher


class AliasPublisher(models.Model):
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    name = models.CharField(max_length=512)
    count = models.IntegerField(default=0)
    unique_together = ('name', 'publisher')

    def __str__(self):
        return self.name + ' --'+str(self.count)+'--> '+str(self.publisher)

    @classmethod
    def increment(cls, name, publisher):
        # TODO it would be more efficient with an update, but it does not really
        # work
        if not name:
            return
        alias, _ = cls.objects.get_or_create(
            name=name, publisher=publisher)
        alias.count += 1
        alias.save()

    class Meta:
        db_table = 'papers_aliaspublisher'
