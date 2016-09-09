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

import datetime
from datetime import date
import doctest

import django.test
from papers.baremodels import BareName
import papers.doi
from papers.models import Name
from papers.models import OaiSource
from papers.models import Paper
from papers.models import Researcher
from papers.baremodels import BareAuthor

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
        r1 = Researcher.create_by_name('Jeanne', 'Harmi')
        n = Name.lookup_name(('Ncersc', 'Harmi'))
        n.save()
        r1.add_name_variant(n, 0.7)
        self.assertAlmostEqual(n.best_confidence, 0.7)
        r1.update_variants(reset=True)
        n = Name.objects.get(pk=n.pk)
        self.assertAlmostEqual(n.best_confidence, 0.)


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(papers.doi))
    return tests


class PaperTest(django.test.TestCase):

    @classmethod
    def setUpClass(self):
        super(PaperTest, self).setUpClass()

    def test_create(self):
        """
        Paper.create checks its arguments are non-empty
        """
        names = [BareName.create('Peter', 'Johnstone'),
                 BareName.create('Xing', 'Li')]
        pubdate = datetime.date(year=2014, month=9, day=4)
        # No title
        self.assertRaises(ValueError, Paper.create,
                          '', names, pubdate)
        # No authors
        self.assertRaises(ValueError, Paper.create,
                          'Excellent title', [], pubdate)
        # No publication date
        self.assertRaises(ValueError, Paper.create,
                          'Excellent title', names, None)
        # Invalid visibility
        self.assertRaises(ValueError, Paper.create,
                          'Excellent title', names, pubdate, visible="something")
        # Not enough affiliations
        self.assertRaises(ValueError, Paper.create,
                          'Excellent title', names, pubdate, affiliations=['ENS'])

    def test_authors(self):
        """
        p.authors returns a non-empty list of BareAuthors
        """
        ist = Paper.create('Groundbreaking Results',
            [BareName.create('Alfred','Kastler'),
             BareName.create('John', 'Dubuc')],
            datetime.date(year=2015, month=3, day=2))
        self.assertGreater(len(ist.authors), 0)
        for a in ist.authors:
            self.assertIsInstance(a, BareAuthor)
            a.check_mandatory_fields()

    def test_add_author(self):
        """
        p.add_author adds the author at the right place
        """
        names = [BareName.create('Peter', 'Johnstone'),
                 BareName.create('Xing', 'Li'),
                 BareName.create('John', 'Dubuc')]
        p = Paper.create('The title', [names[0]],
                             datetime.date(year=2012, month=1, day=9))

        p.add_author(BareAuthor(name=names[2]))
        self.assertEqual(len(p.authors), 2)

        p.add_author(BareAuthor(name=names[1]), position=1)
        self.assertListEqual(p.author_names(), names)

        self.assertRaises(ValueError, p.add_author,
                          BareAuthor(name=BareName.create(
                              'Cantor', 'Bernstein')),
                          position=8)

    def test_displayed_authors(self):
        """
        p.displayed_authors returns a list of authors.
        """
        ist = Paper.create('Groundbreaking Results',
            [BareName.create('Alfred','Kastler'),
             BareName.create('John', 'Dubuc')],
            datetime.date(year=2015, month=3, day=2))
        self.assertEqual(len(ist.displayed_authors()), 2)
        ist.MAX_DISPLAYED_AUTHORS = 1
        self.assertEqual(len(ist.displayed_authors()), 1)


    def test_create_by_doi(self):
        # we recapitalize the DOI to make sure it is treated in a
        # case-insensitive way internally
        p = Paper.create_by_doi('10.1109/sYnAsc.2010.88')
        p.save()
        self.assertEqual(
            p.title, 'Monitoring and Support of Unreliable Services')
        self.assertEqual(p.publications[0].doi, '10.1109/synasc.2010.88')

    def test_publication_pdf_url(self):
        # This paper is gold OA
        p = Paper.create_by_doi('10.1371/journal.pone.0094783')
        p.save()
        # so the pdf_url of the publication should be set
        self.assertNotEqual(p.publications[0].pdf_url, None)

    def test_create_no_authors(self):
        p = Paper.create_by_doi('10.1021/cen-v043n050.p033')
        self.assertEqual(p, None)

    def test_create_invalid_doi(self):
        p = Paper.create_by_doi('10.1021/eiaeuiebop134223cen-v043n050.p033')
        self.assertEqual(p, None)

    def test_merge(self):
        # Get a paper with CrossRef metadata
        p = Paper.create_by_doi('10.1111/j.1744-6570.1953.tb01038.x')
        p.save()
        # Create a copy with slight variations
        names = [BareName.create_bare(f, l) for (f, l) in
                 [('M. H.', 'Jones'), ('R. H.', 'Haase'), ('S. F.', 'Hulbert')]]
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
        self.assertEqual(Paper.objects.filter(
            fingerprint=p.fingerprint).first(), p)
        # The two papers should hence be merged together
        new_paper = p2.recompute_fingerprint_and_merge_if_needed()
        self.assertEqual(new_paper.pk, p.pk)

    def test_attributions_preserved_by_merge(self):
        p1 = Paper.create_by_doi('10.4049/jimmunol.167.12.6786')
        r1 = Researcher.create_by_name('Stephan', 'Hauschildt')
        p1.set_researcher(4, r1.id)
        p2 = Paper.create_by_doi('10.1016/j.chemgeo.2015.03.025')
        r2 = Researcher.create_by_name('Priscille', 'Lesne')
        p2.set_researcher(0, r2.id)

        # merge them ! even if they actually don't have anything
        # to do together
        p1.merge(p2)

        p1.check_authors()
        seen_rids = set()
        for a in p1.authors:
            if a.researcher_id:
                seen_rids.add(a.researcher_id)
        self.assertEqual(seen_rids,
                         set([r1.id, r2.id]))
