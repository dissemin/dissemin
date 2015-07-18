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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __

from django.apps import apps
get_model = apps.get_model

from statistics.models import AccessStatistics

OA_STATUS_CHOICES = (
        ('OA', _('Open access')),
        ('OK', _('Allows pre/post prints')),
        ('NOK', _('Forbids pre/post prints')),
        ('UNK', _('Policy unclear')),
   )

POLICY_CHOICES = [('can', _('Allowed')),
                  ('cannot', _('Forbidden')),
                  ('restricted', _('Restricted')),
                  ('unclear', _('Unclear')),
                  ('unknown', _('Unknown'))]


OA_STATUS_PREFERENCE = [x for x,y in OA_STATUS_CHOICES]

class DummyPublisher(object):
    pk = None
    preprint = 'unknown'
    postprint = 'unknown'
    pdfversion = 'unknown'
    preprint_conditions = []
    postprint_conditions = []
    pdfversion_conditions = []
    def __init__(self):
        pass
    def __unicode__(self):
        return __('Unknown publisher')

default_publisher = DummyPublisher()

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

    class Meta:
        db_table = 'papers_publisher'

    def classify_oa_status(self):
        """
        Classify the publisher status into one of "OA" (gold open access), "OK" (self-archiving permitted for some version),
        "NOK" (self-archiving not allowed), "UNK" (unknown or unclear policy)..
        """
        status = 'UNK'
        lst = [self.preprint, self.postprint, self.pdfversion]
        if 'can' in lst:
            status = 'OK'
        elif 'cannot' in lst and all(map(lambda x: x == 'cannot' or x == 'unknown', lst)):
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
        self.stats.update(get_model('papers', 'Paper').objects.filter(publication__publisher=self).distinct())
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
        papers = get_model('papers', 'Paper').objects.filter(publication__publisher=self.pk)
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
        self.stats.update(get_model('papers', 'Paper').objects.filter(publication__journal=self).distinct())

    def __unicode__(self):
        return self.title
    class Meta:
        ordering = ['title']
        db_table = 'papers_journal'

class PublisherCondition(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=1024)
    def __unicode__(self):
        return self.text
    class Meta:
        db_table = 'papers_publishercondition'

class PublisherCopyrightLink(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    url = models.URLField()
    def __unicode__(self):
        return self.text
    class Meta:
        db_table = 'papers_publishercopyrightlink'

class PublisherRestrictionDetail(models.Model):
    publisher = models.ForeignKey(Publisher)
    text = models.CharField(max_length=256)
    applies_to = models.CharField(max_length=32)
    def __unicode__(self):
        return self.text
    class Meta:
        db_table = 'papers_publisherrestrictiondetail'

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

    class Meta:
        db_table = 'papers_aliaspublisher'


