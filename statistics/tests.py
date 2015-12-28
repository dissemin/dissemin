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
from backend.globals import get_ccf
from backend.crossref import CrossRefPaperSource
from backend.oai import OaiPaperSource
from papers.models import PaperWorld

class StatisticsTest(PrefilledTest):
    @classmethod
    def setUpClass(self):
        super(StatisticsTest, self).setUpClass()
        ccf = get_ccf()
        crps = CrossRefPaperSource(ccf)
        oai = OaiPaperSource(ccf)
        crps.fetch_and_save(self.r2, incremental=True)
        oai.fetch_and_save(self.r2, incremental=True)

    def validStats(self, stats):
        self.assertTrue(stats.check_values())
        self.assertTrue(stats.num_tot > 1)

    def printStats(self, stats):
        print "OA: %d" % stats.num_oa
        print "OK: %d" % stats.num_ok
        print "COULDBE: %d" % stats.num_couldbe
        print "TOT: %d" % stats.num_tot

    def test_researcher(self):
        self.printStats(self.r2.stats)
        self.validStats(self.r2.stats)
    
    def test_department(self):
        self.d.update_stats()
        self.printStats(self.d.stats)
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

