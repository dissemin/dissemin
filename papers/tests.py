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
        self.assertTrue(match_names(('Robin','Ryder'),('Robin','Ryder')))
        self.assertTrue(match_names(('Robin','Ryder'),('R.','Ryder')))
        self.assertTrue(match_names(('R. J.','Ryder'),('R.','Ryder')))
        self.assertFalse(match_names(('Jean', 'Dupont'),('Joseph','Dupont')))
        self.assertFalse(match_names(('R. K.','Ryder'),('J.','Ryder')))

    def test_reverse_order(self):
        self.assertTrue(match_names(('R. J.','Ryder'),('J.','Ryder')))
        self.assertTrue(match_names(('W. T.','Gowers'),('Timothy','Gowers')))

    def test_middle_initial(self):
        self.assertFalse(match_names(('W. T. K.', 'Gowers'),('Timothy', 'Gowers')))

    def test_hyphen(self):
        self.assertTrue(match_names(('J.-P.','Dupont'),('J.','Dupont')))
        self.assertTrue(match_names(('Jean-Pierre','Dupont'),('J.-P.','Dupont')))

    def test_flattened_initials(self):
        self.assertFalse(match_names(('Jamie Oliver','Ryder'),('Jo','Ryder')))
        self.assertTrue(match_names(('Jean-Pierre','Dupont'),('JP.','Dupont')))
        self.assertTrue(match_names(('Jean-Pierre','Dupont'),('Jp.','Dupont')))

    def test_last_name(self):
        self.assertFalse(match_names(('Claire','Mathieu'),('Claire','Kenyon-Mathieu')))

    def test_unicode(self):
        self.assertTrue(match_names(('Thomas Émile','Bourgeat'), ('T. E.','Bourgeat')))

class SplitNameWordsTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(split_name_words('Jean'), (['Jean'],[]))
        self.assertEqual(split_name_words('Jean Pierre'), (['Jean','Pierre'], ['']))
        self.assertEqual(split_name_words('Jean-Pierre'), (['Jean','Pierre'], ['-']))
        self.assertEqual(split_name_words('J.-P.'), (['J','P'], ['-']))
        self.assertEqual(split_name_words('J. P.'), (['J','P'], ['']))

    def test_awkward_spacing(self):
        self.assertEqual(split_name_words('J.P.'), (['J','P'],['']))
        self.assertEqual(split_name_words('J.  P.'), (['J','P'],['']))
        self.assertEqual(split_name_words('Jean - Pierre'), (['Jean','Pierre'],['-']))

    def test_unicode(self):
        self.assertEqual(split_name_words('Émilie'), (['Émilie'],[]))
        self.assertEqual(split_name_words('José'), (['José'],[]))
        self.assertEqual(split_name_words('José Alphonse'), (['José', 'Alphonse'],['']))
        self.assertEqual(split_name_words('É. R.'), (['É','R'],['']))
    
    def test_flattened(self):
        self.assertEqual(split_name_words('JP.'), (['J','P'],['-']))
        self.assertEqual(split_name_words('Jp.'), (['J','P'],['-']))

    def test_probably_not_flattened(self):
        self.assertEqual(split_name_words('Joseph.'), (['Joseph'],[]))

    def test_strange_characters(self):
        self.assertEqual(split_name_words('Jean*-Frederic'), (['Jean','Frederic'],['-']))

class NormalizeNameWordsTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(normalize_name_words('Jean'), 'Jean')
        self.assertEqual(normalize_name_words('Jean-Pierre'), 'Jean-Pierre')
        self.assertEqual(normalize_name_words('John Mark'), 'John Mark')
        self.assertEqual(normalize_name_words('JEAN-PIERRE'), 'Jean-Pierre')
        self.assertEqual(normalize_name_words('JOHN MARK'), 'John Mark')

    def test_unicode(self):
        self.assertEqual(normalize_name_words('JOSÉ'), 'José')
        self.assertEqual(normalize_name_words('JOSÉ-ALAIN'), 'José-Alain')
        self.assertEqual(normalize_name_words('José'), 'José')
        self.assertEqual(normalize_name_words('ÉMILIE'), 'Émilie')
        self.assertEqual(normalize_name_words('Émilie'), 'Émilie')

    def test_spacing(self):
        self.assertEqual(normalize_name_words('John  Mark'), 'John Mark')
        self.assertEqual(normalize_name_words(' John  Mark'), 'John Mark')
        self.assertEqual(normalize_name_words(' John Mark \n'), 'John Mark')
        self.assertEqual(normalize_name_words('Jean - Pierre'), 'Jean-Pierre')
        self.assertEqual(normalize_name_words('J.P. Morgan'), 'J. P. Morgan')

    def test_flattened(self):
        self.assertEqual(normalize_name_words('JP. Morgan'), 'J.-P. Morgan')
        self.assertEqual(normalize_name_words('Jp. Morgan'), 'J.-P. Morgan')

    def test_involutive(self):
        lst = [
                'Jean',
                'Jean-Pierre',
                'John Mark',
                'JEAN-PIERRE',
                'JOHN MARK',
                'JOSÉ',
                'JOSÉ-ALAIN',
                'José',
                'ÉMILIE',
                'Émilie',
                'John  Mark',
                'Jean - Pierre',
                'J.P. Morgan',
                'JP. Morgan',
                'Jp. Morgan',
              ]
        for sample in lst:
            normalized = normalize_name_words(sample)
            self.assertEqual(normalized, normalize_name_words(normalized))

class RecapitalizeWordTest(unittest.TestCase):
    def test_recapitalize_word(self):
        self.assertEqual(recapitalize_word('Dupont'),'Dupont')
        self.assertEqual(recapitalize_word('van'),'van')
        self.assertEqual(recapitalize_word('CLARK'),'Clark')
        self.assertEqual(recapitalize_word('GRANROTH-WILDING'),'Granroth-Wilding')

    def test_unicode(self):
        self.assertEqual(recapitalize_word('ÉMILIE'), 'Émilie')
        self.assertEqual(recapitalize_word('JOSÉ'), 'José')

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
        self.assertEqual(name_unification(('J. P.','Gendre'), ('Jp.','Gendre')), ('J.-P.','Gendre'))
        self.assertEqual(name_unification(('J. Pierre','Gendre'), ('Jp.','Gendre')), ('J.-Pierre','Gendre'))

    def test_empty_first_name(self):
        self.assertEqual(name_unification(('', 'Placet'), ('Vincent', 'Placet')), ('Vincent', 'Placet'))

    def test_name_splitting_error(self):
        # Not sure we can get that right with a reasonable rule
        self.assertEqual(name_unification(('Johannes G. de', 'Vries'), ('Johannes G.','de Vries')),
                ('Johannes G.','de Vries'))
        self.assertEqual(name_unification(('Éric Colin', 'de Verdière'), ('E.','Colin de Verdière')),
                ('Éric','Colin de Verdière'))

