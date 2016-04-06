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
import re
import hashlib
import datetime
import unicode_tex
from unidecode import unidecode
from lxml.html.clean import Cleaner
from lxml.html import fromstring, _transform_result
from lxml import etree
from io import StringIO
from titlecase import titlecase

### General string utilities ###

filter_punctuation_alphanum_regex = re.compile(r'.*\w')
def filter_punctuation(lst):
    """
    :param lst: list of strings
    :returns: all the strings that contain at least one alphanumeric character

    >>> filter_punctuation([u'abc',u'ab.',u'/,',u'a-b',u'#=', u'0'])
    [u'abc', u'ab.', u'a-b', u'0']
    """
    return filter(lambda x: filter_punctuation_alphanum_regex.match(x) is not None,
            lst)

def nocomma(lst):
    """
    Join fields using ',' ensuring that it does not appear in the fields
    This is used to output similarity graphs to be visualized with Gephi.

    :param lst: list of strings
    :returns: these strings joined by commas, ensuring they do not contain
        commas themselves

    >>> nocomma([u'a',u'b',u'cd'])
    u'a,b,cd'
    >>> nocomma([u'a,',u'b'])
    u'a,b'
    >>> nocomma([u'abc',u'',u'\\n',u'def'])
    u'abc, , ,def'
    """
    lst = map(lambda x: str(x).replace(',','').replace('\n',''), lst)
    lst = [x or ' ' for x in lst]
    return ','.join(lst)

def ulower(s):
    """
    Converts to unicode and lowercase.
    :param s: a string
    :return: unicode(s).lower()

    >>> ulower('abSc')
    u'absc'
    >>> ulower(None)
    u'none'
    >>> ulower(89)
    u'89'
    """
    return unicode(s).lower()

def nstrip(s):
    """
    Just like unicode.strip(), but works for None too.

    >>> nstrip(None) is None
    True
    >>> nstrip(u'aa')
    u'aa'
    >>> nstrip(u'  aa \\n')
    u'aa'
    """
    return s.strip() if s else None

def remove_diacritics(s):
    """
    Removes diacritics using the `unidecode` package.

    :param: an str or unicode string
    :returns: if str: the same string. if unicode: the unidecoded string.

    >>> remove_diacritics(u'aéèï')
    'aeei'
    >>> remove_diacritics(u'aéè'.encode('utf-8'))
    'a\\xc3\\xa9\\xc3\\xa8'
    """
    return unidecode(s) if type(s) == unicode else s

def iunaccent(s):
    """
    Removes diacritics and case.

    >>> iunaccent(u'BÉPO forever')
    'bepo forever'
    """
    return remove_diacritics(s).lower()


tokenize_space_re = re.compile(r'\s+')
def tokenize(l):
    """
    A (very very simple) tokenizer.

    >>> tokenize(u'Hello world!')
    [u'Hello', u'world!']
    >>> tokenize(u'99\\tbottles\\nof  beeron \\tThe Wall')
    [u'99', u'bottles', u'of', u'beeron', u'The', u'Wall']
    """
    return tokenize_space_re.split(l)

def maybe_recapitalize_title(title):
    """
    Recapitalize a title if it is mostly uppercase
    (number of uppercase letters > number of lowercase letters)

    >>> maybe_recapitalize_title(u'THIS IS CALLED SCREAMING')
    u'This Is Called Screaming'
    >>> maybe_recapitalize_title(u'This is just a normal title')
    u'This is just a normal title'
    >>> maybe_recapitalize_title(u'THIS IS JUST QUITE Awkward')
    u'THIS IS JUST QUITE Awkward'
    """
    nb_upper, nb_lower = 0, 0
    for letter in title:
        if letter.isupper():
            nb_upper += 1
        elif letter.islower():
            nb_lower += 1

    if nb_upper > nb_lower:
        return titlecase(title)
    else:
        return title

## HTML sanitizing for the title

overescaped_re = re.compile(r'&amp;#(\d+);')
unicode4_re = re.compile(r'(\\u[0-9A-Z]{4})(?![0-9A-Z])')
whitespace_re = re.compile(r'\s+')

html_cleaner = Cleaner()
html_cleaner.allow_tags = ['sub','sup','b','span']
html_cleaner.remove_unknown_tags = False

html_killer = Cleaner()
html_killer.allow_tags = ['div']
html_killer.remove_unknown_tags = False

latexmath_re = re.compile(r'\$(\S[^$]*?\S|\S)\$')
def remove_latex_math_dollars(string):
    """
    Removes LaTeX dollar tags.

    >>> remove_latex_math_dollars(u'This is $\\\\beta$-reduction explained')
    u'This is \\\\beta-reduction explained'
    >>> remove_latex_math_dollars(u'Compare $\\\\frac{2}{3}$ to $\\\\pi$')
    u'Compare \\\\frac{2}{3} to \\\\pi'
    >>> remove_latex_math_dollars(u'Click here to win $100')
    u'Click here to win $100'
    >>> remove_latex_math_dollars(u'What do you prefer, $50 or $100?')
    u'What do you prefer, $50 or $100?'
    """
    return latexmath_re.sub(r'\1', string)

latex_command_re = re.compile(r'(\\([a-zA-Z]+|[.=\'"])({[^}]*})*)')
def unescape_latex(s):
    """
    Replaces LaTeX symbols by their unicode counterparts using
    the `unicode_tex` package.

    >>> unescape_latex(u'the $\\\\alpha$-rays of $\\\\Sigma$-algebras')
    u'the $\\u03b1$-rays of $\\u03a3$-algebras'
    """
    def conditional_replace(fragment):
        rep = unicode_tex.tex_to_unicode_map.get(fragment.group(0))
        return rep or fragment.group(0)

    return latex_command_re.sub(conditional_replace, s)

latex_one_character_braces_re = re.compile(r'(^|(^|[^\\])\b(\w+)){(.)}', re.UNICODE)
latex_full_line_braces_re = re.compile(r'^{(.*)}$')
latex_word_braces_re = re.compile(r'(^|\s){(\w+)}($|\s)', re.UNICODE)
def remove_latex_braces(s):
    """
    Removes spurious braces such as in "Th{é}odore" or "a {CADE} conference"
    This should be run *after* unescape_latex

    >>> remove_latex_braces(u'Th{é}odore')
    u'Th\\xe9odore'
    >>> remove_latex_braces(u'the {CADE} conference')
    u'the CADE conference'
    >>> remove_latex_braces(u'consider 2^{a+b}')
    u'consider 2^{a+b}'
    >>> remove_latex_braces(u'{why these braces?}')
    u'why these braces?'
    """
    s = latex_full_line_braces_re.sub(r'\1', s)
    s = latex_word_braces_re.sub(r'\1\2\3', s)
    s = latex_one_character_braces_re.sub(r'\1\4', s)
    s = latex_one_character_braces_re.sub(r'\1\4', s)
    s = latex_one_character_braces_re.sub(r'\1\4', s)
    return s

def sanitize_html(s):
    """
    Removes most HTML tags, keeping the harmless ones.
    This also renders some LaTeX characters with `unescape_latex`,
    fixes overescaped HTML characters, and a few other fixes.

    >>> sanitize_html('My title<sub>is</sub><a href="http://dissem.in"><sup>nice</sup></a>')
    u'My title<sub>is</sub><sup>nice</sup>'
    >>> sanitize_html('$\\\\alpha$-conversion')
    u'$\\u03b1$-conversion'
    >>> sanitize_html('$$\\\\eta + \\\\omega$$')
    u'$\\u03b7 + \\u03c9$'
    """
    s = overescaped_re.sub(r'&#\1;', s)
    s = unicode4_re.sub(lambda x: x.group(1).decode('unicode-escape'), s)
    s = whitespace_re.sub(r' ', s)
    s = unescape_latex(s)
    s = kill_double_dollars(s)
    orig = html_cleaner.clean_html('<span>'+s+'</span>')
    return orig[6:-7] # We cut the <span />

def kill_html(s):
    """
    Removes every tag except <div> (but there are no
    <div> in titles as sanitize_html removes them)

    >>> kill_html('My title<sub>is</sub><a href="http://dissem.in"><sup>nice</sup>    </a>')
    u'My titleisnice'
    """
    orig = html_killer.clean_html('<div>'+s+'</div>')
    return orig[5:-6].strip() # We cut the <div />

latex_double_dollar_re = re.compile(r'\$\$([^\$]*?)\$\$')
def kill_double_dollars(s):
    """
    Removes double dollars (they generate line breaks with MathJax)
    This is included in the sanitize_html function.

    >>> kill_double_dollars('This equation $$\\\\mathrm{P} = \\\\mathrm{NP}$$ breaks my design')
    u'This equation $\\\\mathrm{P} = \\\\mathrm{NP}$ breaks my design'
    """
    s = latex_double_dollar_re.sub(r'$\1$', s)
    return s

def urlize(val):
    """
    Ensures a would-be URL actually starts with "http://" or "https://".

    :param val: the URL
    :returns: the cleaned URL

    >>> urlize(u'gnu.org')
    u'http://gnu.org'
    >>> urlize(None) is None
    True
    >>> urlize(u'https://gnu.org')
    u'https://gnu.org'
    """
    if val and not val.startswith('http://') and not val.startswith('https://'):
        val = 'http://'+val
    return val

#### JSON utilities !

def jpath(path, js, default=None):
    """
    XPath for JSON!
    
    :param path: a list of keys to follow in the tree of dicts, written in a string,
                separated by forward slashes
    :param default: the default value to return when the key is not found

    >>> jpath(u'message/items', {u'message':{u'items':u'hello'}})
    u'hello'
    """
    def _walk(lst, js):
        if js is None:
            return default
        if lst == []:
            return js
        else:
            return _walk(lst[1:], js.get(lst[0],{} if len(lst) > 1 else default))
    r = _walk(path.split('/'), js)
    return r

def remove_nones(dct):
    """
    Return a dict, without the None values

    >>> remove_nones({u'orcid':None,u'wtf':u'pl'})
    {u'wtf': u'pl'}
    >>> remove_nones({u'orcid':u'blah',u'hey':u'you'})
    {u'orcid': u'blah', u'hey': u'you'}
    >>> remove_nones({None:1})
    {None: 1}
    """
    return dict(filter(lambda (k,v): v is not None, dct.items()))

##### Paper fingerprinting

from papers.name import split_name_words

stripped_chars = re.compile(r'[^- a-z0-9]')
def create_paper_plain_fingerprint(title, authors, year):
    """
    Creates a robust summary of a bibliographic reference.
    This plain fingerprint should then be converted to an
    actual fingerprint by hashing it (so that the length remains
    constant).

    :param title: the title of the paper
    :param authors: the list of author names, represented
        as (first_name, last_name) pairs
    :param year: the year of publication of the paper

    >>> create_paper_plain_fingerprint(' It  cleans whitespace And Case\\n',[('John','Doe')], 2015)
    u'it-cleans-whitespace-and-case/doe'
    >>> create_paper_plain_fingerprint('HTML tags are <emph>removed</emph>',[('John','Doe')], 2015)
    u'html-tags-are-removed/doe'
    >>> create_paper_plain_fingerprint('Les accents sont supprimés', [('John','Doe')],2015)
    u'les-accents-sont-supprimes/doe'
    >>> create_paper_plain_fingerprint('Long titles are unambiguous enough to be unique by themselves, no need for authors', [('John','Doe')], 2015)
    u'long-titles-are-unambiguous-enough-to-be-unique-by-themselves-no-need-for-authors'
    >>> create_paper_plain_fingerprint('Ambiguity', [('John','Doe')], 2014)
    u'ambiguity-2014/doe'
    """
    title = kill_html(title)
    title = remove_diacritics(title).lower()
    title = stripped_chars.sub('',title)
    title = title.strip()
    title = re.sub('[ -]+', '-', title)
    buf = title

    # If the title is long enough, we return the fingerprint as is
    if len(buf) > 50:
        return buf
    
    # If the title is very short, we add the year (for "Preface", "Introduction", "New members" cases)
    #if len(title) <= 16:
    if not '-' in title:
        buf += '-'+str(year)

    author_names_list = []
    for author in authors:
        if not author:
            continue
        author = (remove_diacritics(author[0]),remove_diacritics(author[1]))

        # Last name, without the small words such as "van", "der", "de"…
        last_name_words, last_name_separators = split_name_words(author[1])
        last_words = []
        for i in range(len(last_name_words)):
            if (last_name_words[i][0].isupper() or
                (i > 0 and last_name_separators[i-1] == '-')):
                last_words.append(last_name_words[i])
             
        # If no word was uppercased, fall back on all the words
        if not last_words:
            last_words = last_name_words

        # Lowercase
        last_words = map(ulower, last_words)
        fp = '-'.join(last_words)
        author_names_list.append(fp)

    author_names_list.sort()
    for fp in author_names_list:
        buf += '/'+fp

    return buf

### Partial date representation

def parse_int(val, default):
    """
    Returns an int or a default value if parsing the int failed.

    >>> parse_int(90, None)
    90
    >>> parse_int(None, 90)
    90
    >>> parse_int('est', 8)
    8
    """
    try:
        return int(val)
    except ValueError:
        return default
    except TypeError:
        return default

def date_from_dateparts(dateparts):
    """
    Constructs a date from a list of at most 3 integers.

    >>> date_from_dateparts([])
    datetime.date(1970, 1, 1)
    >>> date_from_dateparts([2015])
    datetime.date(2015, 1, 1)
    >>> date_from_dateparts([2015,02])
    datetime.date(2015, 2, 1)
    >>> date_from_dateparts([2015,02,16])
    datetime.date(2015, 2, 16)
    >>> date_from_dateparts([2015,02,16])
    datetime.date(2015, 2, 16)
    >>> date_from_dateparts([2015,02,35])
    Traceback (most recent call last):
        ...
    ValueError: day is out of range for month
    """
    year = 1970 if len(dateparts) < 1 else parse_int(dateparts[0], 1970)
    month = 01 if len(dateparts) < 2 else parse_int(dateparts[1], 01)
    day = 01 if len(dateparts) < 3 else parse_int(dateparts[2], 01)
    return datetime.date(year=year, month=month, day=day)

def tolerant_datestamp_to_datetime(datestamp):
    """A datestamp to datetime that's more tolerant of diverse inputs.
    Taken from pyoai.

    >>> tolerant_datestamp_to_datetime('2016-02-11T18:34:12Z')
    datetime.datetime(2016, 2, 11, 18, 34, 12)
    >>> tolerant_datestamp_to_datetime('2016-02-11')
    datetime.datetime(2016, 2, 11, 0, 0)
    >>> tolerant_datestamp_to_datetime('2016-02')
    datetime.datetime(2016, 2, 1, 0, 0)
    >>> tolerant_datestamp_to_datetime('2016')
    datetime.datetime(2016, 1, 1, 0, 0)
    >>> tolerant_datestamp_to_datetime('2016-02-11T18:34:12') # Z needed
    Traceback (most recent call last):
        ...
    ValueError: Invalid datestamp: 2016-02-11T18:34:12
    >>> tolerant_datestamp_to_datetime('2016-02-11-3') # too many numbers
    Traceback (most recent call last):
        ...
    ValueError: Invalid datestamp: 2016-02-11-3
    >>> tolerant_datestamp_to_datetime('2016-02-11T18:37:09:38') # too many numbers
    Traceback (most recent call last):
        ...
    ValueError: Invalid datestamp: 2016-02-11T18:37:09:38

    """
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        # if no Z is present, raise error
        if t[-1] != 'Z':
            raise ValueError("Invalid datestamp: "+str(datestamp))
        # split off Z at the end
        t = t[:-1]
    else:
        d = splitted[0]
        t = '00:00:00'
    d_splitted = d.split('-')
    if len(d_splitted) == 3:
        YYYY, MM, DD = d_splitted
    elif len(d_splitted) == 2:
        YYYY, MM = d_splitted
        DD = '01'
    elif len(d_splitted) == 1:
        YYYY = d_splitted[0]
        MM = '01'
        DD = '01'   
    else:
        raise ValueError("Invalid datestamp: "+str(datestamp))
    
    t_splitted = t.split(':')
    if len(t_splitted) == 3:
        hh, mm, ss = t_splitted
    else:
        raise ValueError("Invalid datestamp: "+str(datestamp))
    return datetime.datetime(
        int(YYYY), int(MM), int(DD), int(hh), int(mm), int(ss))

### ORCiD utilities ###

orcid_re = re.compile(r'^(http://orcid.org/)?([0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9])$')

def validate_orcid(orcid):
    """
    :returns: a cleaned ORCiD if the argument represents a valid ORCiD, None otherwise

    This does not check that the id actually exists on orcid.org,
    only checks that it is syntactically valid (including the checksum).
    See http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier

    See the test suite for a more complete set of examples

    >>> validate_orcid(u' 0000-0001-8633-6098\\n')
    u'0000-0001-8633-6098'
    """
    if not orcid:
        return
    try:
        orcid = unicode(orcid).strip()
    except ValueError, TypeError:
        return

    match = orcid_re.match(orcid)
    if not match:
        return
    orcid = match.group(2)
    nums = orcid.replace('-','')
    total = 0
    for i in range(15):
        total = (total + int(nums[i])) * 2
    checkdigit = (12 - (total % 11)) % 11
    checkchar = str(checkdigit) if checkdigit != 10 else 'X'
    if nums[-1] == checkchar:
        return orcid

def affiliation_is_greater(a, b):
    """
    Compares to affiliation values. Returns True
    when the first contains more information than
    the second

    >>> affiliation_is_greater(None, None)
    False
    >>> affiliation_is_greater(None, 'UPenn')
    False
    >>> affiliation_is_greater('UPenn', None)
    True
    >>> affiliation_is_greater('0000-0001-8633-6098', 'Ecole normale superieure, Paris')
    True
    >>> affiliation_is_greater('Ecole normale superieure', 'Upenn')
    True
    """
    if a is None:
        return False
    if b is None:
        return True
    oa, ob = validate_orcid(a), validate_orcid(b)
    if oa and not ob:
        return True
    if ob and not oa:
        return False
    return len(a) > len(b)


# List utilities

def index_of(elem, choices):
    """
    Returns the index of elem (understood as a code) in the list of choices,
    where choices are expected to be pairs of (code,verbose_description). 

    >>> index_of(42, [])
    0
    >>> index_of('ok', [('ok','This is ok'),('nok','This is definitely not OK')])
    0
    >>> index_of('nok', [('ok','This is ok'),('nok','This is definitely not OK')])
    1
    """
    for idx, (code, lbl) in enumerate(choices):
        if code == elem:
            return idx
    else:
        return 0
