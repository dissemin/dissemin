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
import unittest

import django.test

from papers.baremodels import *
import papers.doi


class BareObjectTest(unittest.TestCase):
    """
    Base class for tests on BareObjects.
    Subclasses should reimplement setUp
    to create a test instance in self.ist.
    """

    def setUp(self):
        self.ist = None
        raise unittest.SkipTest('Base test')

    def test_breadcrumbs(self):
        for name, url in self.ist.breadcrumbs():
            self.assertIsInstance(name, unicode)
            self.assertIsInstance(url, unicode)

    def test_mandatory_fields(self):
        self.ist.check_mandatory_fields()


class BarePaperTest(BareObjectTest):
    """
    Tests methods of BarePaper objects
    """

    def setUp(self):
        self.ist = BarePaper.create('Groundbreaking Results',
                                    [BareName.create('Alfred', 'Kastler'),
                                     BareName.create('John', 'Dubuc')],
                                    datetime.date(year=2015, month=3, day=2))

    def test_create(self):
        """
        BarePaper.create checks its arguments are non-empty
        """
        names = [BareName.create('Peter', 'Johnstone'),
                 BareName.create('Xing', 'Li')]
        pubdate = datetime.date(year=2014, month=9, day=4)
        # No title
        self.assertRaises(ValueError, BarePaper.create,
                          '', names, pubdate)
        # No authors
        self.assertRaises(ValueError, BarePaper.create,
                          'Excellent title', [], pubdate)
        # No publication date
        self.assertRaises(ValueError, BarePaper.create,
                          'Excellent title', names, None)
        # Invalid visibility
        self.assertRaises(ValueError, BarePaper.create,
                          'Excellent title', names, pubdate, visible="something")
        # Not enough affiliations
        self.assertRaises(ValueError, BarePaper.create,
                          'Excellent title', names, pubdate, affiliations=['ENS'])

    def test_authors(self):
        """
        p.authors returns a non-empty list of BareAuthors
        """
        self.assertGreater(len(self.ist.authors), 0)
        for a in self.ist.authors:
            self.assertIsInstance(a, BareAuthor)
            a.check_mandatory_fields()

    def test_add_author(self):
        """
        p.add_author adds the author at the right place
        """
        names = [BareName.create('Peter', 'Johnstone'),
                 BareName.create('Xing', 'Li'),
                 BareName.create('John', 'Dubuc')]
        p = BarePaper.create('The title', [names[0]],
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
        self.assertEqual(len(self.ist.displayed_authors()), 2)
        self.ist.MAX_DISPLAYED_AUTHORS = 1
        self.assertEqual(len(self.ist.displayed_authors()), 1)


class BareOaiRecordTest(unittest.TestCase):
    def test_cleanup_desc(self):
        r = BareOaiRecord()

        r.description = "International audience ; While price and data…"
        r.cleanup_description()
        self.assertEqual(r.description, "While price and data…")

        r.description = " Abstract: While price and data…"
        r.cleanup_description()
        self.assertEqual(r.description, "While price and data…")
