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
    def num_available(self):
        return self.num_oa + self.num_ok
    @property
    def num_unavailable(self):
        return self.num_couldbe + self.num_unk + self.num_closed

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
    @property
    def percentage_available(self):
        if self.num_tot:
            return int(100.*(self.num_oa + self.num_ok)/self.num_tot)
    @property
    def percentage_unavailable(self):
        if self.num_tot:
            return int(100.*(self.num_couldbe + self.num_unk + self.num_closed)/self.num_tot)
            

    @classmethod
    def update_all_stats(self, _class):
        for x in _class.objects.all():
            x.update_stats()

    class Meta:
        db_table = 'papers_accessstatistics'

