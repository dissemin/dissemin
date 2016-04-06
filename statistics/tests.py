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
from backend.crossref import CrossRefPaperSource
from backend.oai import OaiPaperSource
from papers.models import PaperWorld, Paper
from statistics.models import *

class StatisticsTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(StatisticsTest, self).setUpClass()
        self.ccf.clear()
        crps = CrossRefPaperSource(self.ccf)
        oai = OaiPaperSource(self.ccf)
        crps.fetch_and_save(self.r2, incremental=True)
        oai.fetch_and_save(self.r2, incremental=True)

    def validStats(self, stats):
        self.assertTrue(stats.check_values())
        self.assertTrue(stats.num_tot > 1)

    def test_researcher(self):
        self.validStats(self.r2.stats)

    def test_from_queryset(self):
        bare_stats = BareAccessStatistics.from_queryset(
                Paper.objects.filter(author__researcher=self.r2).distinct())
        stats = self.r2.stats
        self.assertEqual(bare_stats.num_oa, stats.num_oa)
        self.assertEqual(bare_stats.num_ok, stats.num_ok)
        self.assertEqual(bare_stats.num_couldbe, stats.num_couldbe)
        self.assertEqual(bare_stats.num_unk, stats.num_unk)
        self.assertEqual(bare_stats.num_closed, stats.num_closed)
        self.assertEqual(bare_stats.num_tot, stats.num_tot)
    
    def test_department(self):
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

