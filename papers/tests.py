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
from papers.name import *

class MatchNamesTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(match_names(('Robin','Ryder'),('Robin','Ryder')), True)
        self.assertEqual(match_names(('Robin','Ryder'),('R.','Ryder')), True)
        self.assertEqual(match_names(('R. J.','Ryder'),('R.','Ryder')), True)
        self.assertEqual(match_names(('Jean', 'Dupont'),('Joseph','Dupont')), False)
        self.assertEqual(match_names(('R. K.','Ryder'),('J.','Ryder')), False)

    def test_reverse_order(self):
        self.assertEqual(match_names(('R. J.','Ryder'),('J.','Ryder')), True)
        self.assertEqual(match_names(('W. T.','Gowers'),('Timothy','Gowers')), True)

    def test_hyphen(self):
        self.assertEqual(match_names(('J.-P.','Dupont'),('J.','Dupont')), True)
        self.assertEqual(match_names(('Jean-Pierre','Dupont'),('J.-P.','Dupont')), True)

    def test_flattened_initials(self):
        self.assertEqual(match_names(('Jamie Oliver','Ryder'),('Jo','Ryder')), False)
        self.assertEqual(match_names(('Jean-Pierre','Dupont'),('JP.','Dupont')), True)
        self.assertEqual(match_names(('Jean-Pierre','Dupont'),('Jp.','Dupont')), True)

    def test_last_name(self):
        self.assertEqual(match_names(('Claire','Mathieu'),('Claire','Kenyon-Mathieu')), False)

class RecapitalizeWordTest(unittest.TestCase):
    def test_recapitalize_word(self):
        self.assertEqual(recapitalize_word('Dupont'),'Dupont')
        self.assertEqual(recapitalize_word('van'),'van')
        self.assertEqual(recapitalize_word('CLARK'),'Clark')
        self.assertEqual(recapitalize_word('GRANROTH-WILDING'),'Granroth-Wilding')

class ParseCommaNameTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_comma_name('Claire Mathieu'), ('Claire', 'Mathieu'))
        self.assertEqual(parse_comma_name('Mathieu, Claire'), ('Claire', 'Mathieu'))
        self.assertEqual(parse_comma_name('Kenyon-Mathieu, Claire'), ('Claire', 'Kenyon-Mathieu'))
        self.assertEqual(parse_comma_name('Arvind'), ('', 'Arvind'))

    def test_initial_capitalized(self):
        self.assertEqual(parse_comma_name('MATHIEU Claire'), ('Claire', 'Mathieu'))
        self.assertEqual(parse_comma_name('MATHIEU C.'), ('C.', 'Mathieu'))

    def test_final_capitalized(self):
        self.assertEqual(parse_comma_name('Claire MATHIEU'), ('Claire', 'Mathieu'))
        self.assertEqual(parse_comma_name('C. MATHIEU'), ('C.', 'Mathieu'))

    def test_initial_initials(self):
        self.assertEqual(parse_comma_name('C. Mathieu'), ('C.', 'Mathieu'))
        self.assertEqual(parse_comma_name('N. E. Young'), ('N. E.', 'Young'))

    def test_final_initials(self):
        self.assertEqual(parse_comma_name('Mathieu C.'), ('C.', 'Mathieu'))
        self.assertEqual(parse_comma_name('Gowers W. T..'), ('W. T.', 'Gowers'))

    def test_middle_initials(self):
        self.assertEqual(parse_comma_name('Neal E. Young'), ('Neal E.', 'Young'))

    def test_hard_cases(self):
        self.assertEqual(parse_comma_name('W. Timothy Gowers'), ('W. Timothy', 'Gowers'))
        self.assertEqual(parse_comma_name('Guido van Rossum'), ('Guido', 'van Rossum'))
        self.assertEqual(parse_comma_name('Éric Colin de Verdière'), ('Éric', 'Colin de Verdière'))

class NameUnificationTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(name_unification(('Jean','Dupont'), ('Jean','Dupont')), ('Jean','Dupont'))
        self.assertEqual(name_unification(('J.','Dupont'), ('Jean','Dupont')), ('Jean','Dupont'))
        self.assertEqual(name_unification(('Anna','Erscher'), ('A. G.','Erscher')), ('Anna G.','Erscher'))

    def test_hyphens(self):
        self.assertEqual(name_unification(('J.-P.','Dupont'), ('Jean','Dupont')), ('Jean-P.','Dupont'))
        self.assertEqual(name_unification(('Jean Pierre','Dupont'), ('Jean','Dupont')),
                ('Jean Pierre','Dupont'))
        self.assertEqual(name_unification(('Jean-Pierre','Dupont'), ('Jean','Dupont')),
                ('Jean-Pierre','Dupont'))

    def test_uncommon_order(self):
        self.assertEqual(name_unification(('W. T.','Gowers'), ('Timothy','Gowers')), ('W. Timothy','Gowers'))

    def test_flattened_initials(self):
        self.assertEqual(name_unification(('J. P.','Gendre'), ('Jp.','Gendre')), ('J. P.','Gendre'))

    def test_empty_first_name(self):
        self.assertEqual(name_unification(('', 'Placet'), ('Vincent', 'Placet')), ('Vincent', 'Placet'))

    def test_name_splitting_error(self):
        self.assertEqual(name_unification(('Johannes G. de', 'Vries'), ('Johannes G.','de Vries')),
                ('Johannes G.','de Vries'))

    def test_strange_characters(self):
        self.assertEqual(name_unification(('Jean*-Frederic', 'Colombel'),('Jean-Frederic','Colombel')),
                ('Jean-Frederic','Colombel'))
