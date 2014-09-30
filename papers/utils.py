# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import re
import hashlib
import unicodedata

def match_names(a,b):
    (firstA,lastA) = a
    (firstB,lastB) = b
    return lastA.lower() == lastB.lower() and match_first_names(firstA,firstB)

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

def remove_diacritics(s):
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore')

split_re = re.compile(r'[ .,]*')
def split_words(string):
    return filter(lambda x: x != '', split_re.split(string))

initial_re = re.compile(r'[A-Z](\.,;)*$')
def normalize_name_words(w):
    """ If it is an initial, ensure it is of the form "T.", and recapitalize it. """
    words = w.split()
    words = map(recapitalize_word, words)
    words = map(lambda w: w[0]+'.' if initial_re.match(w) else w, words)
    return ' '.join(words)

def recapitalize_word(w):
    """ Turns every word fully capitalized into an uncapitalized word (except for the first character) """
    return w[0]+w[1:].lower() if all(map(isupper, w)) else w

def match_first_names(a,b):
    partsA = split_words(a)
    partsB = split_words(b)
    partsA = map(unicode.lower, partsA)
    partsB = map(unicode.lower, partsB)
    return partsA == partsB
# TODO : add support for initials ?
# but this might include a lot of garbage

def to_plain_name(name):
    return (name.first,name.last)

stripped_chars = re.compile(r'[^- a-z0-9]')
def create_paper_fingerprint(title, authors):
    title = title.lower()
    title = stripped_chars.sub('',title)
    title = title.strip()
    title = re.sub(' ', '-', title)
    buf = title

    for author in authors:
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
        buf += '/'+fp

    m = hashlib.md5()
    m.update(remove_diacritics(buf))
    return m.hexdigest()





