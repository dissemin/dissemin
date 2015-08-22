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
from papers.name import *
from papers.utils import unescape_latex, remove_latex_math_dollars, validate_orcid, remove_latex_braces

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

    def test_abbreviation(self):
        self.assertEqual(split_name_words('Ms.'), (['Ms.'],[]))
        self.assertEqual(split_name_words('St. Louis'), (['St.', 'Louis'],['']))

    def test_probably_not_flattened(self):
        self.assertEqual(split_name_words('Joseph.'), (['Joseph'],[]))

    @unittest.expectedFailure
    def test_strange_characters(self):
        # TODO ?
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
        self.assertEqual(normalize_name_words('J.P.'), 'J. P.')

    def test_flattened(self):
        self.assertEqual(normalize_name_words('JP.'), 'J.-P.')
        self.assertEqual(normalize_name_words('Jp.'), 'J.-P.')

    def test_comma(self):
        self.assertEqual(normalize_name_words('John, Mark'), 'John Mark')
        self.assertEqual(normalize_name_words('John,, Mark'), 'John Mark')
        self.assertEqual(normalize_name_words('John Mark,'), 'John Mark')
        self.assertEqual(normalize_name_words('John Mark,,'), 'John Mark')
        self.assertEqual(normalize_name_words('John, Mark,,'), 'John Mark')

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

    @unittest.expectedFailure
    def test_hard_cases(self):
        # TODO ?
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
    
    @unittest.expectedFailure
    def test_name_splitting_error(self):
        # TODO Not sure we can get that right with a reasonable rule
        self.assertEqual(name_unification(('Johannes G. de', 'Vries'), ('Johannes G.','de Vries')),
                ('Johannes G.','de Vries'))
        self.assertEqual(name_unification(('Éric Colin', 'de Verdière'), ('E.','Colin de Verdière')),
                ('Éric','Colin de Verdière'))

class UnifyNameListsTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(unify_name_lists([],[]),[])
        self.assertEqual(unify_name_lists(
            [('Jean','Dupont')],
            [('Jean','Dupont')]),
            [(('Jean','Dupont'),(0,0))])
        self.assertEqual(unify_name_lists(
            [('Jean','Dupont')],
            [('J.','Dupont')]),
            [(('Jean','Dupont'),(0,0))])
        self.assertEqual(unify_name_lists(
            [('Jean','Dupont')],
            [('J. F.','Dupont')]),
            [(('Jean F.','Dupont'),(0,0))])
        self.assertEqual(unify_name_lists(
            [('Jean','Dupont'),('Marie','Dupré'),('Alphonse','de Lamartine')],
            [('J.','Dupont'),('M.','Dupré'),('A.','de Lamartine')]),
            [(('Jean','Dupont'),(0,0)),(('Marie','Dupré'),(1,1)),(('Alphonse','de Lamartine'),(2,2))])

    def test_insertion(self):
        self.assertEqual(unify_name_lists(
            [('Jean','Dupont'),('Marie','Dupré'),('Alphonse','de Lamartine')],
            [('J.','Dupont'),('M.','Dupré'),('A.','de Lamartine'),('R.','Badinter')]),
            [(('Jean','Dupont'),(0,0)),(('Marie','Dupré'),(1,1)),
                (('Alphonse','de Lamartine'),(2,2)),(('R.','Badinter'),(None,3))])
        self.assertEqual(unify_name_lists(
            [('Élise','Chaumont'),('Jean','Dupont'),('Marie','Dupré'),('Alphonse','de Lamartine')],
            [('J.','Dupont'),('M.','Dupré'),('A.','de Lamartine')]),
            [(('Élise','Chaumont'),(0,None)),(('Jean','Dupont'),(1,0)),(('Marie','Dupré'),(2,1)),(('Alphonse','de Lamartine'),(3,2))])

    def test_same_last_name(self):
        self.assertTrue(unify_name_lists(
            [('Jean','Dupont'),('Marie','Dupont')],
            [('M.','Dupont'),('J. P.','Dupont')]) in
            [
                 [(('Jean P.','Dupont'),(0,1)),(('Marie','Dupont'),(1,0))],
                 [(('Marie','Dupont'),(1,0)),(('Jean P.','Dupont'),(0,1))]    
            ])

class UnescapeLatexTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(unescape_latex('This is a test'), 'This is a test')
        self.assertEqual(unescape_latex('This is an \\alpha ray'), 'This is an α ray')
        self.assertEqual(unescape_latex('This is an $\\alpha$ ray'), 'This is an $α$ ray')

    def test_remove_latex_math_dollars(self):
        self.assertEqual(remove_latex_math_dollars('This is an $α$ test'), 'This is an α test')
        self.assertEqual(remove_latex_math_dollars('This is an $α + x$ test'), 'This is an α + x test')

    def test_dollar_present(self):
        self.assertEqual(unescape_latex('The revenue is $30 per cow'), 'The revenue is $30 per cow')
        self.assertEqual(remove_latex_math_dollars('The revenue is $30 per cow'),
                'The revenue is $30 per cow')
        self.assertEqual(remove_latex_math_dollars('Instead of $15, the revenue is $30 per cow'),
                'Instead of $15, the revenue is $30 per cow')

class RemoveLatexBracesTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(remove_latex_braces('this is a test'), 'this is a test')
        self.assertEqual(remove_latex_braces('this is a {Test}'), 'this is a Test')
        self.assertEqual(remove_latex_braces('this {is} a Test'), 'this is a Test')
        self.assertEqual(remove_latex_braces('{this} is a Test'), 'this is a Test')
        self.assertEqual(remove_latex_braces('{this is a Test}'), 'this is a Test')

    def test_unicode(self):
        self.assertEqual(remove_latex_braces('th{í}s is a Test'), 'thís is a Test')
        self.assertEqual(remove_latex_braces('{t}hís is a Test'), 'thís is a Test')
        self.assertEqual(remove_latex_braces('thís {is} a Test'), 'thís is a Test')

    def test_math(self):
        self.assertEqual(remove_latex_braces('base^{superscript}_{subscript}'), 'base^{superscript}_{subscript}')

    def test_command(self):
        self.assertEqual(remove_latex_braces('in \\mathbb{R} let'), 'in \\mathbb{R} let')
        self.assertEqual(remove_latex_braces('in \\emph{blue} let'), 'in \\emph{blue} let')

    def test_multiple(self):
        self.assertEqual(remove_latex_braces('J{é}r{é}mie'), 'Jérémie')

class ValidateOrcidTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(validate_orcid(None), None)
        self.assertEqual(validate_orcid(189), None)
        self.assertEqual(validate_orcid('rst'), None)
        self.assertEqual(validate_orcid('0123012301230123'), None)

    def test_checksum(self):
        self.assertEqual(validate_orcid('0000-0002-8612-8827'), '0000-0002-8612-8827')
        self.assertEqual(validate_orcid('0000-0002-8612-8828'), None)
        self.assertEqual(validate_orcid('0000-0001-5892-743X'), '0000-0001-5892-743X')
        self.assertEqual(validate_orcid('0000-0001-5892-7431'), None)

    def test_whitespace(self):
        self.assertEqual(validate_orcid('\t0000-0002-8612-8827  '), '0000-0002-8612-8827')

