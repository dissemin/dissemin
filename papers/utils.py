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

from time import sleep
import socket
from urllib2 import urlopen, build_opener
from nltk.tokenize.punkt import PunktWordTokenizer

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

punktTokenizer = PunktWordTokenizer()

def tokenize(l):
    return punktTokenizer.tokenize(iunaccent(l))


##### Paper fingerprinting

stripped_chars = re.compile(r'[^- a-z0-9]')
def create_paper_plain_fingerprint(title, authors):
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
    retries = kwargs.get('retries', 4)
    delay = kwargs.get('delay', 5)
    backoff = kwargs.get('backoff', 2)
    opener = kwargs.get('opener', build_opener())
    try:
        return opener.open(url, data, timeout)
    except socket.timeout:
        if retries <= 0:
            raise
    print "Retrying in "+str(delay)+" seconds..."
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

