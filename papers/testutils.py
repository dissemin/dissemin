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

from papers.utils import unescape_latex, remove_latex_math_dollars, validate_orcid, remove_latex_braces, kill_double_dollars

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

class KillDoubleDollarsTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(kill_double_dollars('Fast Exhaustive Search for Quadratic Systems in $$\\mathbb {F}_{2}$$ on FPGAs'), 'Fast Exhaustive Search for Quadratic Systems in $\\mathbb {F}_{2}$ on FPGAs')

    def test_multiple(self):
        self.assertEqual(kill_double_dollars('$$\\textit{K}$$ -trivial, $$\\textit{K}$$ -low and $${{\\mathrm{\\textit{MLR}}}}$$ -low Sequences: A Tutorial'), '$\\textit{K}$ -trivial, $\\textit{K}$ -low and ${{\\mathrm{\\textit{MLR}}}}$ -low Sequences: A Tutorial')


