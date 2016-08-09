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

import doctest
import unittest

import papers.fingerprint
from papers.utils import unescape_latex, kill_double_dollars, validate_orcid
from papers.utils import affiliation_is_greater, jpath
from papers.utils import remove_latex_math_dollars, remove_latex_braces

class UnescapeLatexTest(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(unescape_latex('This is a test'), 'This is a test')
        self.assertEqual(unescape_latex(
            'This is an \\alpha ray'), 'This is an α ray')
        self.assertEqual(unescape_latex(
            'This is an $\\alpha$ ray'), 'This is an $α$ ray')

    def test_remove_latex_math_dollars(self):
        self.assertEqual(remove_latex_math_dollars(
            'This is an $α$ test'), 'This is an α test')
        self.assertEqual(remove_latex_math_dollars(
            'This is an $α + x$ test'), 'This is an α + x test')

    def test_dollar_present(self):
        self.assertEqual(unescape_latex(
            'The revenue is $30 per cow'), 'The revenue is $30 per cow')
        self.assertEqual(remove_latex_math_dollars('The revenue is $30 per cow'),
                         'The revenue is $30 per cow')
        self.assertEqual(remove_latex_math_dollars('Instead of $15, the revenue is $30 per cow'),
                         'Instead of $15, the revenue is $30 per cow')

    def test_crazy_accents(self):
        self.assertEqual(unescape_latex("Cohomologie locale des faisceaux coh\\'erents et th\\'eor\\`emes de Lefschetz locaux et globaux (SGA 2)"),
                         "Cohomologie locale des faisceaux cohérents et théorèmes de Lefschetz locaux et globaux (SGA 2)")


class RemoveLatexBracesTest(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(remove_latex_braces(
            'this is a test'), 'this is a test')
        self.assertEqual(remove_latex_braces(
            'this is a {Test}'), 'this is a Test')
        self.assertEqual(remove_latex_braces(
            'this {is} a Test'), 'this is a Test')
        self.assertEqual(remove_latex_braces(
            '{this} is a Test'), 'this is a Test')
        self.assertEqual(remove_latex_braces(
            '{this is a Test}'), 'this is a Test')

    def test_unicode(self):
        self.assertEqual(remove_latex_braces(
            'th{í}s is a Test'), 'thís is a Test')
        self.assertEqual(remove_latex_braces(
            '{t}hís is a Test'), 'thís is a Test')
        self.assertEqual(remove_latex_braces(
            'thís {is} a Test'), 'thís is a Test')

    def test_math(self):
        self.assertEqual(remove_latex_braces(
            'base^{superscript}_{subscript}'), 'base^{superscript}_{subscript}')

    def test_command(self):
        self.assertEqual(remove_latex_braces(
            'in \\mathbb{R} let'), 'in \\mathbb{R} let')
        self.assertEqual(remove_latex_braces(
            'in \\emph{blue} let'), 'in \\emph{blue} let')

    def test_multiple(self):
        self.assertEqual(remove_latex_braces('J{é}r{é}mie'), 'Jérémie')


class KillDoubleDollarsTest(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(kill_double_dollars(
            'Fast Exhaustive Search for Quadratic Systems in $$\\mathbb {F}_{2}$$ on FPGAs'), 'Fast Exhaustive Search for Quadratic Systems in $\\mathbb {F}_{2}$ on FPGAs')

    def test_multiple(self):
        self.assertEqual(kill_double_dollars('$$\\textit{K}$$ -trivial, $$\\textit{K}$$ -low and $${{\\mathrm{\\textit{MLR}}}}$$ -low Sequences: A Tutorial'),
                         '$\\textit{K}$ -trivial, $\\textit{K}$ -low and ${{\\mathrm{\\textit{MLR}}}}$ -low Sequences: A Tutorial')


class ValidateOrcidTest(unittest.TestCase):

    def test_simple(self):
        self.assertEqual(validate_orcid(None), None)
        self.assertEqual(validate_orcid(189), None)
        self.assertEqual(validate_orcid('rst'), None)
        self.assertEqual(validate_orcid('0123012301230123'), None)

    def test_checksum(self):
        self.assertEqual(validate_orcid('0000-0002-8612-8827'),
                         '0000-0002-8612-8827')
        self.assertEqual(validate_orcid('0000-0002-8612-8828'), None)
        self.assertEqual(validate_orcid('0000-0001-5892-743X'),
                         '0000-0001-5892-743X')
        self.assertEqual(validate_orcid('0000-0001-5892-7431'), None)

    def test_whitespace(self):
        self.assertEqual(validate_orcid(
            '\t0000-0002-8612-8827  '), '0000-0002-8612-8827')

    def test_url(self):
        self.assertEqual(validate_orcid(
            'http://orcid.org/0000-0002-8612-8827'), '0000-0002-8612-8827')


class UtilitiesTest(unittest.TestCase):

    def test_affiliation_is_greater_partial_order(self):
        for a, b in [(None, None), (None, 'Cambridge'), ('0000-0002-8612-8827', 'ENS'),
                     ('University of Oxford, Oxfordshire', '0000-0001-5892-7431')]:
            self.assertFalse(affiliation_is_greater(a, b) and
                             affiliation_is_greater(b, a))
            self.assertFalse(affiliation_is_greater(a, a))
            self.assertFalse(affiliation_is_greater(b, b))

    def test_jpath(self):
        self.assertEqual(jpath('awesome', {}), None)
        self.assertEqual(jpath('awesome', {}, 41), 41)
        self.assertEqual(jpath('a', {'a': 'b'}, 41), 'b')
        self.assertEqual(jpath('a/b', {'a': {'b': 7}, 'c': None}, 41), 7)
        self.assertEqual(jpath('a', {'a': {'b': 7}, 'c': None}, 41), {'b': 7})


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(papers.utils))
    tests.addTests(doctest.DocTestSuite(papers.fingerprint))
    return tests
