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
Tests statistics update and statistics consistency.
"""

from django.test import TestCase
from backend.tests import PrefilledTest
from backend.orcid import OrcidPaperSource
from papers.models import PaperWorld, Paper
from statistics.models import *

class StatisticsTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(StatisticsTest, self).setUpClass()
        crps = OrcidPaperSource()
        crps.fetch_and_save(self.r3)

    def validStats(self, stats):
        self.assertTrue(stats.check_values())
        self.assertTrue(stats.num_tot > 1)

    def test_researcher(self):
        self.validStats(self.r3.stats)

    def test_from_queryset(self):
        bare_stats = BareAccessStatistics.from_queryset(
                Paper.objects.filter(authors_list__contains=[{'researcher_id':self.r2.id}]).distinct())
        stats = self.r2.stats
        self.assertEqual(bare_stats.num_oa, stats.num_oa)
        self.assertEqual(bare_stats.num_ok, stats.num_ok)
        self.assertEqual(bare_stats.num_couldbe, stats.num_couldbe)
        self.assertEqual(bare_stats.num_unk, stats.num_unk)
        self.assertEqual(bare_stats.num_closed, stats.num_closed)
        self.assertEqual(bare_stats.num_tot, stats.num_tot)
    
    def test_department(self):
        self.r3.department = self.d
        self.r3.save()
        self.d.update_stats()
        self.validStats(self.d.stats)

    def test_institution(self):
        self.i.update_stats()
        self.validStats(self.i.stats)

    def test_paperworld(self):
        pw = PaperWorld.get_solo()
        pw.update_stats()
        self.validStats(pw.stats)

# TODO check journal and publisher stats
# TODO check that (for instance) department stats add up to institution stats

