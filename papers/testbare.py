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

from papers.baremodels import BareAuthor
from papers.baremodels import BareName
from papers.baremodels import BareOaiRecord
from papers.models import Paper


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



class BareOaiRecordTest(unittest.TestCase):

    def test_cleanup_desc(self):
        r = BareOaiRecord()

        r.description = "International audience ; While price and data…"
        r.cleanup_description()
        self.assertEqual(r.description, "While price and data…")

        r.description = " Abstract: While price and data…"
        r.cleanup_description()
        self.assertEqual(r.description, "While price and data…")

        r.description = None
        r.cleanup_description()
        self.assertEqual(r.description, None)
