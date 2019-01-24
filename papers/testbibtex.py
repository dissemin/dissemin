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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
#
from __future__ import unicode_literals

import unittest

from papers.bibtex import parse_authors_list, parse_bibtex


class ParseAuthorsListTest(unittest.TestCase):
    def test_simple(self):
        record = {
            'author': 'Claire Toffano-Nioche and Daniel Gautheret and Fabrice Leclerc'
        }
        self.assertEqual(
            parse_authors_list(record),
            {
                'author': [
                    ('Claire', 'Toffano-Nioche'),
                    ('Daniel', 'Gautheret'),
                    ('Fabrice', 'Leclerc')
                ]
            }
        )

    def test_etal(self):
        record = {
            'author': 'Claire Toffano-Nioche and et al.'
        }
        self.assertEqual(
            parse_authors_list(record),
            {
                'author': [('Claire', 'Toffano-Nioche')]
            }
        )

    def test_others(self):
        record = {
            'author': 'Claire Toffano-Nioche and others'
        }
        self.assertEqual(
            parse_authors_list(record),
            {
                'author': [('Claire', 'Toffano-Nioche')]
            }
        )


class ParseBibtexTest(unittest.TestCase):
    def test_parse_bibtex(self):
        bibtex = """@misc{ Nobody06,
    author = "Orti, E. and Bredas, J.L. and Clarisse, C. and others",
    title = "My Article",
    year = "2006" }
        """
        self.assertEqual(
            parse_bibtex(bibtex),
            {
                'ENTRYTYPE': 'misc',
                'ID': 'Nobody06',
                'author': [
                    ('E.', 'Orti'),
                    ('J. L.', 'Bredas'),
                    ('C.', 'Clarisse')
                ],
                'title': 'My Article',
                'year': '2006'
            }
        )

    def test_parse_bibtex_unicode_accents(self):
        """
        See https://github.com/dissemin/dissemin/issues/362
        """
        bibtex = """@misc{ Nobody06,
    author = "Adrià Martin Mor",
    title = "My Article",
    year = "2006" }
        """
        self.assertEqual(
            parse_bibtex(bibtex),
            {
                'ENTRYTYPE': 'misc',
                'ID': 'Nobody06',
                'author': [(u'Adrià Martin', u'Mor')],
                'title': 'My Article',
                'year': '2006'
            }
        )

    def test_parse_bibtex_latex_accents(self):
        """
        See https://github.com/dissemin/dissemin/issues/362
        """
        bibtex = r"""@misc{Nobody06,
    author = "Adri{\`{a}} Mart{\'{\i}}n Mor and Alessandro Beccu",
    title = "My Article",
    year = "2006" }
        """
        print(parse_bibtex(bibtex)['author'][0][0])
        self.assertEqual(
            parse_bibtex(bibtex),
            {
                'ENTRYTYPE': 'misc',
                'ID': 'Nobody06',
                'author': [
                    ('Adrià Martín', 'Mor'),
                    ('Alessandro', 'Beccu')
                ],
                'title': 'My Article',
                'year': '2006'
            }
        )
