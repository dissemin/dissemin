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
from papers.bibtex import parse_authors_list

class ParseAuthorsListTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_authors_list('Claire Toffano-Nioche and Daniel Gautheret and Fabrice Leclerc'),
                [('Claire','Toffano-Nioche'),('Daniel','Gautheret'),('Fabrice','Leclerc')])

    def test_etal(self):
        self.assertEqual(parse_authors_list('Claire Toffano-Nioche and et al.'),
                [('Claire','Toffano-Nioche')])


