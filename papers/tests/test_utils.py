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




import unittest
import datetime

from papers.utils import affiliation_is_greater
from papers.utils import jpath
from papers.utils import kill_double_dollars
from papers.utils import remove_latex_braces
from papers.utils import remove_latex_math_dollars
from papers.utils import unescape_latex
from papers.utils import validate_orcid
from papers.utils import filter_punctuation
from papers.utils import date_from_dateparts
from papers.utils import datetime_to_date
from papers.utils import ulower
from papers.utils import nstrip
from papers.utils import nocomma
from papers.utils import remove_diacritics
from papers.utils import iunaccent
from papers.utils import tokenize
from papers.utils import urlize
from papers.utils import sanitize_html
from papers.utils import maybe_recapitalize_title
from papers.utils import kill_html
from papers.utils import remove_nones
from papers.utils import extract_domain
from papers.utils import parse_int
from papers.utils import tolerant_datestamp_to_datetime
from papers.utils import valid_publication_date
from papers.utils import index_of



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

    def test_filter_punctuation(self):
        self.assertEqual(filter_punctuation(['abc','ab.','/,','a-b','#=', '0']),
                            ['abc', 'ab.', 'a-b', '0'])

    def test_nocomma(self):
        self.assertEqual(nocomma(['a','b','cd']), 'a,b,cd')
        self.assertEqual(nocomma(['a,','b']), 'a,b')
        self.assertEqual(nocomma(['abc','','\n','def']), 'abc, , ,def')

    def test_ulower(self):
        self.assertEqual(ulower('abSc'), 'absc')
        self.assertEqual(ulower(None), 'none')
        self.assertEqual(ulower(89), '89')

    def test_nstrip(self):
        self.assertTrue(nstrip(None) is None)
        self.assertEqual(nstrip('aa'), 'aa')
        self.assertEqual(nstrip('  aa \n'), 'aa')

    def test_remove_diacritics(self):
        self.assertEqual(remove_diacritics('aéèï'), 'aeei')
        self.assertEqual(remove_diacritics('aéè'.encode('utf-8')), b'a\xc3\xa9\xc3\xa8')

    def test_iunaccent(self):
            self.assertEqual(iunaccent('BÉPO forever'), 'bepo forever')

    def test_tokenize(self):
        self.assertEqual(tokenize('Hello world!'), ['Hello', 'world!'])
        self.assertEqual(tokenize('99\tbottles\nof  beeron \tThe Wall'), ['99', 'bottles', 'of', 'beeron', 'The', 'Wall'])

    def test_maybe_recapitalize_title(self):
        self.assertEqual(maybe_recapitalize_title('THIS IS CALLED SCREAMING'), 'This Is Called Screaming')
        self.assertEqual(maybe_recapitalize_title('This is just a normal title'), 'This is just a normal title')
        self.assertEqual(maybe_recapitalize_title('THIS IS JUST QUITE Awkward'), 'THIS IS JUST QUITE Awkward')

    def test_remove_latex_math_dollars(self):
        self.assertEqual(remove_latex_math_dollars('This is $\\beta$-reduction explained'), 'This is \\beta-reduction explained')
        self.assertEqual(remove_latex_math_dollars('Compare $\\frac{2}{3}$ to $\\\\pi$'), 'Compare \\frac{2}{3} to \\\\pi')
        self.assertEqual(remove_latex_math_dollars('Click here to win $100'), 'Click here to win $100')
        self.assertEqual(remove_latex_math_dollars('What do you prefer, $50 or $100?'), 'What do you prefer, $50 or $100?')

    def test_unescape_latex(self):
        self.assertEqual(unescape_latex('the $\\alpha$-rays of $\\Sigma$-algebras'), 'the $\u03b1$-rays of $\u03a3$-algebras')
        self.assertEqual(unescape_latex('$\\textit{K}$ -trivial'), '$\\textit{K}$ -trivial')

    def test_remove_latex_braces(self):
        self.assertEqual(remove_latex_braces('Th{é}odore'), 'Th\xe9odore')
        self.assertEqual(remove_latex_braces('the {CADE} conference'), 'the CADE conference')
        self.assertEqual(remove_latex_braces('consider 2^{a+b}'), 'consider 2^{a+b}')
        self.assertEqual(remove_latex_braces('{why these braces?}'), 'why these braces?')

    def test_sanitize_html(self):
        self.assertEqual(sanitize_html('My title<sub>is</sub><a href="http://dissem.in"><sup>nice</sup></a>'), 'My title<sub>is</sub><sup>nice</sup>')
        self.assertEqual(sanitize_html('$\\alpha$-conversion'), '$\u03b1$-conversion')
        self.assertEqual(sanitize_html('$$\\eta + \\omega$$'), '$\u03b7 + \u03c9$')
        self.assertEqual(sanitize_html('abc & def'), 'abc &amp; def')
        self.assertEqual(sanitize_html('Universitat Aut\\uFFFDnoma de Barcelona'), 'Universitat Aut�noma de Barcelona')

    def test_kill_html(self):
        self.assertEqual(kill_html('My title<sub>is</sub><a href="http://dissem.in"><sup>nice</sup>    </a>'), 'My titleisnice')

    def test_kill_double_dollars(self):
        self.assertEqual(kill_double_dollars('This equation $$\\mathrm{P} = \\mathrm{NP}$$ breaks my design'), 'This equation $\\mathrm{P} = \\mathrm{NP}$ breaks my design')

    def test_urlize(self):
        self.assertEqual(urlize('gnu.org'), 'http://gnu.org')
        self.assertTrue(urlize(None) is None)
        self.assertEqual(urlize(u'https://gnu.org'), 'https://gnu.org')

    def test_extract_domain(self):
        self.assertEqual(extract_domain('https://gnu.org/test.html'), 'gnu.org')
        self.assertTrue(extract_domain('nonsense') is None)

    def test_remove_nones(self):
        self.assertEqual(remove_nones({'orcid':None,'wtf':'pl'}), {'wtf': 'pl'})
        self.assertEqual(remove_nones({'orcid':'blah','hey':'you'}), {'orcid': 'blah', 'hey': 'you'})
        self.assertEqual(remove_nones({None:1}), {None: 1})

    def test_parse_int(self):
        self.assertEqual(parse_int(90, None), 90)
        self.assertEqual(parse_int(None, 90), 90)
        self.assertEqual(parse_int('est', 8), 8)

    def test_date_from_dateparts(self):
        self.assertEqual(date_from_dateparts([]), datetime.date(1970, 1, 1))
        self.assertEqual(date_from_dateparts([2015]), datetime.date(2015, 1, 1))
        self.assertEqual(date_from_dateparts([2015,2]), datetime.date(2015, 2, 1))
        self.assertEqual(date_from_dateparts([2015,2,16]), datetime.date(2015, 2, 16))
        self.assertEqual(date_from_dateparts([2015,2,16]), datetime.date(2015, 2, 16))
        with self.assertRaises(ValueError):
            date_from_dateparts([2015,2,35])

    def tolerant_datestamp_to_datetime(self):
        self.assertEqual(tolerant_datestamp_to_datetime('2016-02-11T18:34:12Z'), datetime.datetime(2016, 2, 11, 18, 34, 12))
        self.assertEqual(tolerant_datestamp_to_datetime('2016-02-11'), datetime.datetime(2016, 2, 11, 0, 0))
        self.assertEqual(tolerant_datestamp_to_datetime('2016/02/11'), datetime.datetime(2016, 2, 11, 0, 0))
        self.assertEqual(tolerant_datestamp_to_datetime('2016-02'), datetime.datetime(2016, 2, 1, 0, 0))
        self.assertEqual(tolerant_datestamp_to_datetime('2016'), datetime.datetime(2016, 1, 1, 0, 0))
        with self.assertRaises(ValueError):
            tolerant_datestamp_to_datetime('2016-02-11T18:34:12') # Z needed
        with self.assertRaises(ValueError):
            tolerant_datestamp_to_datetime('2016-02-11-3') # too many numbers
        with self.assertRaises(ValueError):
            tolerant_datestamp_to_datetime('2016-02-11T18:37:09:38') # too many numbers
        with self.assertRaises(ValueError):
            tolerant_datestamp_to_datetime('20151023371')
        with self.assertRaises(ValueError):
            tolerant_datestamp_to_datetime('2014T')

    def test_datetime_to_date(self):
        self.assertEqual(datetime_to_date(datetime.datetime(2016, 2, 11, 18, 34, 12)), datetime.date(2016, 2, 11))
        self.assertEqual(datetime_to_date(datetime.date(2015, 3, 1)), datetime.date(2015, 3, 1))

    def test_valid_publication_date(self):
        self.assertEqual(valid_publication_date(datetime.date(6789, 1, 1)), False)
        self.assertEqual(valid_publication_date(datetime.date(2018, 3, 4)), True)
        self.assertEqual(valid_publication_date(None), False)

    def test_validate_orcid(self):
        self.assertEqual(validate_orcid(' 0000-0001-8633-6098\n'), '0000-0001-8633-6098')

    def test_affiliation_is_greater(self):
        self.assertEqual(affiliation_is_greater(None, None), False)
        self.assertEqual(affiliation_is_greater(None, 'UPenn'), False)
        self.assertEqual(affiliation_is_greater('UPenn', None), True)
        self.assertEqual(affiliation_is_greater('0000-0001-8633-6098', 'Ecole normale superieure, Paris'), True)
        self.assertEqual(affiliation_is_greater('Ecole normale superieure', 'Upenn'), True)

    def test_index_of(self):
        self.assertEqual(index_of(42, []), 0)
        self.assertEqual(index_of('ok', [('ok','This is ok'),('nok','This is definitely not OK')]), 0)
        self.assertEqual(index_of('nok', [('ok','This is ok'),('nok','This is definitely not OK')]), 1)

