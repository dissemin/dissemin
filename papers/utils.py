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
from unidecode import unidecode
from lxml.html.clean import Cleaner
from lxml.html import fromstring, _transform_result
from lxml import etree
from io import StringIO

### General string utilities ###

filter_punctuation_alphanum_regex = re.compile(r'\w')
def filter_punctuation(lst):
    return filter(lambda x: filter_punctuation_alphanum_regex.findall(x) != [], lst)

def nocomma(lst):
    """
    Join fields using ',' ensuring that it does not appear in the fields
    """
    lst = map(lambda x: str(x).replace(',','').replace('\n',''), lst)
    lst = [x if x else ' ' for x in lst]
    return ','.join(lst)

split_re = re.compile(r'[ .,-]*')
def split_words(string):
    return filter(lambda x: x != '', split_re.split(string))

def ulower(s):
    return unicode(s).lower()

def isupper(s):
    if type(s) == type(u''):
        return unicode.isupper(s)
    else:
        return str.isupper(s)

def nstr(s):
    if s:
        return s
    return ''

def nstrip(s):
    if s:
        return s.strip()
    return None

def remove_diacritics(s):
    if type(s) == type(u''):
        return unidecode(s)
    else:
        return s

def iunaccent(s):
    return remove_diacritics(s).lower()


tokenize_space_re = re.compile(r'\s+')
def fallback_tokenize(l):
    return tokenize_space_re.split(l)

try:
    from nltk.tokenize import word_tokenize
    tokenize = word_tokenize
except ImportError:
    tokenize = fallback_tokenize
except LookupError:
    tokenize = fallback_tokenize

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

def unescape_latex(s):
    # TODO: replace this by a proper LaTeX unescaping algorithm (hence increasing the coverage)
    s = s.replace("\\'e","é")
    s = s.replace("\\`e","è")
    s = s.replace("\\`a","à")
    s = s.replace('\\"o',"ö")
    s = s.replace('\\"a',"ä")
    s = s.replace('\\"e',"ë")
    s = s.replace('\\"{\\i}',"ï")
    s = s.replace('\\^{o}',"ô")
    s = s.replace('\\^{a}',"â")
    s = s.replace('\\^{e}',"ê")
    s = s.replace('\\^{i}',"î")
    s = s.replace("\\'{E}","É")
    s = s.replace("\\`{E}","È")
    s = s.replace("\\`{A}","À")
    s = s.replace('\\"{O}',"Ö")
    s = s.replace('\\^{O}',"Ô")
    s = s.replace('\\"{A}',"Ä")
    return s

def sanitize_html(s):
    s = overescaped_re.sub(r'&#\1;', s)
    s = unicode4_re.sub(lambda x: x.group(1).decode('unicode-escape'), s)
    s = whitespace_re.sub(r' ', s)
    s = unescape_latex(s)
    orig = html_cleaner.clean_html('<span>'+s+'</span>')
    return orig[6:-7]

def kill_html(s):
    """
    Removes every tag except <div> (but there are no
    <div> in titles as sanitize_html removes them)
    """
    orig = html_killer.clean_html('<div>'+s+'</div>')
    return orig[5:-6]


##### Paper fingerprinting

stripped_chars = re.compile(r'[^- a-z0-9]')
def create_paper_plain_fingerprint(title, authors):
    title = kill_html(title)
    title = remove_diacritics(title).lower()
    title = stripped_chars.sub('',title)
    title = title.strip()
    title = re.sub('[ -]+', '-', title)
    buf = title

    author_names_list = []
    for author in authors:
        if not author:
            continue
        # TODO remove the - in "J.-W. Dupont" TODO TODO
        # TODO take into account only the first initial
        author = (remove_diacritics(author[0]),remove_diacritics(author[1]))
        # Initials of the given names
        initials = map(lambda x: x[0].lower(), split_words(author[0]))
        # Last name, without the small words such as "van", "der", "de"…
        # TODO: remove this filter
        last_words = filter(lambda x: x[0].isupper(), split_words(author[1]))
        # If no word was uppercased, fall back on all the words
        if not last_words:
            last_words = split_words(author[1])
        # Lowercase
        last_words = map(ulower, last_words)
        fp = ('-'.join(initials))+'-'+('-'.join(last_words))
        author_names_list.append(fp)

    author_names_list.sort()
    for fp in author_names_list:
        buf += '/'+fp

    print "Fingerprint: "+buf
    return buf

def create_paper_fingerprint(title, authors):
    m = hashlib.md5()
    m.update(create_paper_plain_fingerprint(title, authors))
    return m.hexdigest()

### Partial date representation

def parse_int(val, default):
    try:
        return int(val)
    except ValueError:
        return default
    except TypeError:
        return default

def date_from_dateparts(dateparts):
    year = 1970 if len(dateparts) < 1 else parse_int(dateparts[0], 1970)
    month = 01 if len(dateparts) < 2 else parse_int(dateparts[1], 01)
    day = 01 if len(dateparts) < 3 else parse_int(dateparts[2], 01)
    return datetime.date(year=year, month=month, day=day)

def tolerant_datestamp_to_datetime(datestamp):
    """A datestamp to datetime that's more tolerant of diverse inputs.
    Taken from pyoai.

    Not used inside pyoai itself right now, but can be used when defining
    your own metadata schema if that has a broader variety of datetimes
    in there.
    """
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        # if no Z is present, raise error
        if t[-1] != 'Z':
            raise DatestampError(datestamp)
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
