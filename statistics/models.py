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
This module defines the :class:`AccessStatistics` model. It stores statistics
about the accessiblity status of papers related to any model
(currently :class:`.Researcher`, :class:`.Journal`, :class:`.Publisher`,
:class:`.Department`, :class:`.Institution` and :class:`.PaperWorld`).

As all these modules are spread in different apps and link to :class:`AccessStatistics`,
this model has been separated from the rest for dependency reasons.

The different states a paper can have are defined in :py:obj:`COMBINED_STATUS_CHOICES`
(where a human-readable description is given), :py:obj:`STATUS_QUERYSET_FILTER`
(where the corresponding QuerySet filters are defined) and in :py:func:`combined_status_for_instance`
which computes the status of a particular paper.
"""

from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

#: Paper status (combined because it takes into account
#: both the publisher policy and the full text availability).
#:
#: If these states are changed, then the filters :py:obj:`STATUS_QUERYSET_FILTER`
#: have to be updated, as well as :py:func:`combined_status_for_instance`.
COMBINED_STATUS_CHOICES = [
    ('oa', _('Available from the publisher')),
    ('ok', _('Available from the author')),
    ('couldbe', _('Could be shared by the authors')),
    ('unk', _('Unknown/unclear sharing policy')),
    ('closed', _('Publisher forbids sharing')),
    ]

#: Helptext displayed when a paper logo is hovered
STATUS_CHOICES_HELPTEXT = {
    'oa': _('This paper is made freely available by the publisher.'),
    'ok': _('This paper is available in a repository.'),
    'couldbe': _('This paper was not found in any repository, but could be made available legally by the author.'),
    'unk': _('This paper was not found in any repository; the policy of its publisher is unknown or unclear.'),
    'closed': _('Distributing this paper is prohibited by the publisher'),
    }

#: Availability status choices
PDF_STATUS_CHOICES = [('OK', _('Available')),
                      ('NOK', _('Unavailable'))]

#: Filters associated to each combined status choice
#: These filters, once applied to a queryset of Papers,
#: select the papers in the given state.
STATUS_QUERYSET_FILTER = {
    'oa': lambda q: q.filter(oa_status='OA'),
    'ok': lambda q: q.filter(Q(pdf_url__isnull=False) & ~Q(oa_status='OA')),
    'couldbe': lambda q: q.filter(pdf_url__isnull=True, oa_status='OK'),
    'unk': lambda q: q.filter(pdf_url__isnull=True, oa_status='UNK'),
    'closed': lambda q: q.filter(pdf_url__isnull=True, oa_status='NOK'),
    }


def combined_status_for_instance(paper):
    """
    Computes the current combined status of a given paper.
    This is defined here so that the function can be easily updated when
    we change :py:obj:`STATUS_QUERYSET_FILTER` or :py:obj:`COMBINED_STATUS_CHOICES`.
    """
    if paper.oa_status == 'OA':
        return 'oa'
    elif paper.pdf_url:
        return 'ok'
    else:
        if paper.oa_status == 'OK':
            return 'couldbe'
        elif paper.oa_status == 'NOK':
            return 'closed'
    return 'unk'


def combined_status_stats(queryset):
    aggregations = queryset.get_aggregation_results()
    status = aggregations.get('status', {'buckets':[]})
    buckets = {
        bucket['key']: bucket['doc_count']
        for bucket in status['buckets']
    }
    return BareAccessStatistics.from_dict(buckets)


class BareAccessStatistics(object):
    """
    A bare summary of the status of a set of publications
    """
    @classmethod
    def new(cls):
        """
        Creates an empty object (all counters set to 0)
        """
        s = cls()
        s.clear()
        return s

    def clear(self):
        """
        Sets all counters to zero
        """
        self.num_oa = 0
        self.num_ok = 0
        self.num_couldbe = 0
        self.num_unk = 0
        self.num_closed = 0
        self.num_tot = 0

    def add(self, other):
        """
        Adds the stats of `other` to self (sum of access statistics)
        """
        self.num_oa += other.num_oa
        self.num_ok += other.num_ok
        self.num_couldbe += other.num_couldbe
        self.num_unk += other.num_unk
        self.num_closed += other.num_closed
        self.num_tot += other.num_tot

    @classmethod
    def from_queryset(cls, qs):
        """
        This method fetches all the queryset.

        :param qs: a queryset of :class:`~papers.models.Paper` objects
        :returns: an object of the current class,
                  with the status of all papers in this queryset.
        """
        stats = cls.new()
        for paper in qs:
            stats.num_tot += 1
            attrname = 'num_'+paper.combined_status
            setattr(stats, attrname, getattr(stats, attrname) + 1)
        return stats

    @classmethod
    def from_dict(cls, d):
        stats = cls.new()
        for status, count in d.iteritems():
            stats.num_tot += count
            setattr(stats, 'num_'+status, count)
        return stats

    def check_values(self):
        """
        Checks that values are consistent (non-negative and summing up to the total).
        """
        return (
                self.num_oa >= 0 and
                self.num_ok >= 0 and
                self.num_couldbe >= 0 and
                self.num_unk >= 0 and
                self.num_closed >= 0 and
                self.num_oa + self.num_ok + self.num_couldbe +
                  self.num_unk + self.num_closed == self.num_tot
                )

    def pie_data(self):
        """
        Returns a dictionary containing the data needed to display
        the statistics as a pie.
        """
        detailed_data = []
        for (key, desc) in COMBINED_STATUS_CHOICES:
            item = {
                'id': key,
                'label': unicode(desc),
                'value': self.__dict__['num_'+key],
                }
            detailed_data.append(item)
        # Gives the translated label
        aggregated_labels = []
        for (key, desc) in PDF_STATUS_CHOICES:
            item = {'label': unicode(desc)}
            aggregated_labels.append(item)
        return {'detailed': detailed_data, 'aggregated': aggregated_labels}

    @property
    def num_available(self):
        """
        Total number of available items (from publisher or author)
        """
        return self.num_oa + self.num_ok

    @property
    def num_unavailable(self):
        """
        Total number of unavailable items
        """
        return self.num_couldbe + self.num_unk + self.num_closed

    @property
    def percentages(self):
        """
        A dictionary whose keys are the identifiers for the paper states
        and whose values are the percentages of these states for the given statistics.
        """
        if self.num_tot:
            return {key: 100.*self.__dict__['num_'+key]/self.num_tot for key in STATUS_QUERYSET_FILTER}

    @property
    def percentage_available(self):
        """
        Percentage of available items
        """
        if self.num_tot:
            return int(100.*(self.num_oa + self.num_ok)/self.num_tot)

    @property
    def percentage_unavailable(self):
        """
        Percentage of unavailable items
        """
        if self.num_tot:
            return int(100.*(self.num_couldbe + self.num_unk + self.num_closed)/self.num_tot)


class AccessStatistics(models.Model, BareAccessStatistics):
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
        Updates the statistics for papers contained in the given :py:class:`Paper` queryset
        """
        queryset = queryset.filter(visible=True)
        for key, modifier in STATUS_QUERYSET_FILTER.items():
            self.__dict__['num_'+key] = modifier(queryset).count()
        self.num_tot = queryset.count()
        self.save()

    @classmethod
    def update_all_stats(self, _class):
        """
        Update all statistics for the objects of a given class.
        This calls the underlying :py:meth:`!update_stats()` function for each instance
        of the model.
        """
        for x in _class.objects.all():
            x.update_stats()

    class Meta:
        db_table = 'papers_accessstatistics'
