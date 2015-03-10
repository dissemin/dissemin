# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
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

from time import sleep
import socket
import httplib
import urllib2
from httplib import HTTPException
from urllib2 import urlopen, build_opener, URLError

from papers.errors import MetadataSourceException


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


try:
    from nltk.tokenize.punkt import PunktWordTokenizer
    punktTokenizer = PunktWordTokenizer()
    def tokenize(l):
        return punktTokenizer.tokenize(iunaccent(l))
except ImportError:
    tokenize_space_re = re.compile(r'\s+')
    def tokenize(l):
        return tokenize_spae_re.split(l)

## HTML sanitizing for the title

overescaped_re = re.compile(r'&amp;#(\d+);')
whitespace_re = re.compile(r'\s+')

html_cleaner = Cleaner()
html_cleaner.allow_tags = ['sup','b','span']
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



### Open an URL with retries

def urlopen_retry(url, **kwargs):# data, timeout, retries, delay, backoff):
    data = kwargs.get('data', None)
    timeout = kwargs.get('timeout', 10)
    retries = kwargs.get('retries', 3)
    delay = kwargs.get('delay', 5)
    backoff = kwargs.get('backoff', 2)
    headers = kwargs.get('headers', {})
    opener = kwargs.get('opener', build_opener())
    try:
        req = urllib2.Request(url, data, headers)
        return opener.open(req, data, timeout)
    except socket.timeout as e:
        if retries <= 0:
            raise MetadataSourceException('timeout: '+str(e))
    except URLError as e:
        if retries <= 0:
            raise MetadataSourceException('URL error: '+str(e))
    except HTTPException as e:
        if retries <= 0:
            raise MetadataSourceException('HTTP error: '+str(e))

    print "Retrying in "+str(delay)+" seconds..."
    print "URL: "+url
    sleep(delay)
    return urlopen_retry(url,
            data=data,
            timeout=timeout,
            retries=retries-1,
            delay=delay*backoff,
            backoff=backoff)

### Partial date representation

def date_from_dateparts(dateparts):
    year = 1970 if len(dateparts) < 1 else dateparts[0]
    month = 01 if len(dateparts) < 2 else dateparts[1]
    day = 01 if len(dateparts) < 3 else dateparts[2]
    return datetime.date(year=year, month=month, day=day)

