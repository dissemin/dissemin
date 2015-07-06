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
from backend.romeo import *
from backend.oai import *
from backend.tasks import *
from papers.models import *
from publishers.models import *

from lxml import etree

# SHERPA/RoMEO interface
class RomeoTest(TestCase):
    def test_perform_query(self):
        self.assertIsInstance(perform_romeo_query({'issn':'0022-328X'}), etree._ElementTree)
        self.assertIsInstance(perform_romeo_query({'jtitle':'Physical Review E'}), etree._ElementTree)

    def test_fetch_journal(self):
        terms = {'issn':'0022-328X'}
        orig_terms = terms.copy()
        self.assertIsInstance(fetch_journal(terms), Journal)
        self.assertEqual(terms, orig_terms)
        journal = find_journal_in_model(terms)
        self.assertIsInstance(journal, Journal)
        self.assertEqual(journal.issn, terms['issn'])

    def test_unicode(self):
        terms = {'issn':'0375-0906'}
        journal = fetch_journal(terms)
        self.assertEqual(journal.title, 'Revista de Gastroenterología de México')
        self.assertEqual(journal.publisher.name, 'Elsevier España')

    def test_openaccess(self):
        self.assertEqual(fetch_journal({'issn':'1471-2105'}).publisher.oa_status, 'OA')
        self.assertEqual(fetch_journal({'issn':'1951-6169'}).publisher.oa_status, 'OA')

    def test_closed(self):
        self.assertEqual(fetch_journal({'issn':'0732-183X'}).publisher.oa_status, 'NOK')

    def test_open(self):
        self.assertEqual(fetch_journal({'issn':'1631-073X'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal({'issn':'0099-2240'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal({'issn':'0036-8075'}).publisher.oa_status, 'OK')

# Generic test case that requires some example DB
class PrefilledTest(TestCase):
    def setUp(self):
        self.d = Department.objects.create(name='Chemistry dept')
        self.r1 = Researcher.create_from_scratch('Isabelle', 'Aujard', self.d, None, None, None)
        self.r2 = Researcher.create_from_scratch('Ludovic', 'Jullien', self.d, None, None, None)
        self.hal = OaiSource.objects.create(identifier='hal',
                name='HAL',
                default_pubtype='preprint')

# Test that the CORE interface works
class CoreTest(PrefilledTest):
    def test_core_interface_works(self):
        fetch_papers_from_core_for_researcher(self.r1)

# Test that the CrossRef interface works
class CrossRefTest(PrefilledTest):
    def test_crossref_interface_works(self):
        fetch_dois_for_researcher(self.r1.pk)

# Test that the proaixy interface works
class ProaixyTest(PrefilledTest):
    def test_proaixy_interface_works(self):
        fetch_records_for_researcher(self.r1.pk)

