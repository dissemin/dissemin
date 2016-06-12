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

import unittest
import django.test
from datetime import date
from papers.models import *
import papers.doi
import datetime
import json

class ResearcherTest(django.test.TestCase):
    def test_creation(self):
        r = Researcher.create_by_name('Marie', 'Farge')
        r2 = Researcher.create_by_name(' Marie', ' Farge')
        self.assertNotEqual(r, r2)

        r3 = Researcher.get_or_create_by_orcid('0000-0002-4445-8625')
        self.assertNotEqual(r, r3)

    def test_name_conflict(self):
        # Both are called "John Doe"
        r1 = Researcher.get_or_create_by_orcid('0000-0001-7295-1671')
        r2 = Researcher.get_or_create_by_orcid('0000-0001-5393-1421')
        self.assertNotEqual(r1, r2)

    def test_clear_name_variants(self):
        r1 = Researcher.create_by_name('Jeanne','Harmi')
        n = Name.lookup_name(('Ncersc','Harmi'))
        n.save()
        r1.add_name_variant(n, 0.7)
        self.assertAlmostEqual(n.best_confidence, 0.7)
        r1.update_variants(reset=True)
        n = Name.objects.get(pk=n.pk)
        self.assertAlmostEqual(n.best_confidence, 0.)

class OaiRecordTest(django.test.TestCase):
    @classmethod
    def setUpClass(self):
        super(OaiRecordTest, self).setUpClass()
        self.source = OaiSource.objects.get_or_create(identifier='arxiv',
                defaults={'name':'arXiv','oa':False,'priority':1,'default_pubtype':'preprint'})

    def test_find_duplicate_records_invalid_url(self):
        paper = Paper.get_or_create('this is a title', [Name.lookup_name(('Jean','Saisrien'))],
                datetime.date(year=2015,month=05,day=04))
        # This used to throw an exception
        OaiRecord.find_duplicate_records(paper, 'ftp://dissem.in/paper.pdf', None)

import doctest
def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(papers.doi))
    return tests


class PaperTest(django.test.TestCase):
    @classmethod
    def setUpClass(self):
        super(PaperTest, self).setUpClass()

    def test_create_by_doi(self):
        p = Paper.create_by_doi('10.1109/synasc.2010.88')
        p = Paper.from_bare(p)
        self.assertEqual(p.title, 'Monitoring and Support of Unreliable Services')
        self.assertEqual(p.publications[0].doi, '10.1109/synasc.2010.88')

    def test_publication_pdf_url(self):
        # This paper is gold OA
        p = Paper.create_by_doi('10.1007/BF02702259')
        p = Paper.from_bare(p)
        # so the pdf_url of the publication should be set
        self.assertEqual(p.publications[0].pdf_url.lower(), 'http://dx.doi.org/10.1007/BF02702259'.lower())

    def test_create_no_authors(self):
        p = Paper.create_by_doi('10.1021/cen-v043n050.p033')
        self.assertEqual(p, None)

    def test_create_invalid_doi(self):
        p = Paper.create_by_doi('10.1021/eiaeuiebop134223cen-v043n050.p033')
        self.assertEqual(p, None)

    def test_merge(self):
        # Get a paper with CrossRef metadata
        p = Paper.create_by_doi('10.1111/j.1744-6570.1953.tb01038.x')
        p = Paper.from_bare(p)
        # Create a copy with slight variations
        names = map(Name.lookup_name, [('M. H.','Jones'),('R. H.', 'Haase'),('S. F.','Hulbert')])
        p2 = Paper.get_or_create(
                'A Survey of the Literature on Technical Positions', names,
                date(year=2011, month=01, day=01))
        # The two are not merged because of the difference in the title
        self.assertNotEqual(p, p2)
        # Fix the title of the second one
        p2.title = 'A Survey of the Literature on Job Analysis of Technical Positions'
        p2.save()
        # Check that the new fingerprint is equal to that of the first paper
        self.assertEqual(p2.new_fingerprint(), p.fingerprint)
        # and that the new fingerprint and the current differ
        self.assertNotEqual(p2.new_fingerprint(), p2.fingerprint)
        # and that the first paper matches its own shit
        self.assertEqual(Paper.objects.filter(fingerprint=p.fingerprint).first(), p)
        # The two papers should hence be merged together
        new_paper = p2.recompute_fingerprint_and_merge_if_needed()
        self.assertEqual(new_paper.pk, p.pk)




