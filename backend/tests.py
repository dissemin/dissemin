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

from django.test import TestCase
from backend.core import *
from backend.crossref import *
from backend.oai import *
from backend.tasks import *
from papers.models import *

# Generic test case that requires some example DB

class PrefilledTest(TestCase):
    def fillDB(self):
        self.d = Department.objects.create(name='Chemistry dept')
        self.r1 = Researcher.create_from_scratch('Isabelle', 'Aujard', self.d, None, None, None)
        self.r2 = Researcher.create_from_scratch('Ludovic', 'Jullien', self.d, None, None, None)
        self.hal = OaiSource.objects.create(identifier='hal',
                name='HAL',
                default_pubtype='preprint')

# Test that the CORE interface works
class CoreTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_core_interface_works(self):
        fetch_papers_from_core_for_researcher(self.r1)

# Test that the CrossRef interface works
class CrossRefTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_crossref_interface_works(self):
        fetch_dois_for_researcher(self.r1.pk)

# Test that the proaixy interface works
class ProaixyTest(PrefilledTest):
    def setUp(self):
        self.fillDB()

    def test_proaixy_interface_works(self):
        fetch_records_for_researcher(self.r1.pk)

