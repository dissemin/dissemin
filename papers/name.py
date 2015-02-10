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
import name_tools

from papers.utils import split_words, iunaccent, remove_diacritics, isupper

# Name managemement: heuristics to separate a name into (first,last)
comma_re = re.compile(r',+')
space_re = re.compile(r'\s+')
initial_re = re.compile(r'(^|\W)\w(\W|$)')
lowercase_re = re.compile(r'[a-z]')
letter_re = re.compile(r'\w')

def match_names(a,b):
    """
    Returns a boolean: are these two names compatible?
    Examples:
    > ('Robin', 'Ryder'),('R.', 'Ryder'): True
    > ('Robin J.', 'Ryder'),('R.', 'Ryder'): True
    > ('R. J.', 'Ryder'),('J.', 'Ryder'): False
    > ('Claire', 'Mathieu'),('Claire', 'Kenyon-Mathieu'): False
    """
    if not a or not b:
        return False
    (firstA,lastA) = a
    (firstB,lastB) = b
    if lastA.lower() != lastB.lower():
        return False
    partsA = split_words(firstA)
    partsB = split_words(firstB)
    parts = zip(partsA, partsB)
    return all(map(match_first_names, parts))

initial_re = re.compile(r'[A-Z](\.,;)*$')
def normalize_name_words(w):
    """ If it is an initial, ensure it is of the form "T.", and recapitalize fully capitalized words. """
    w = w.strip()
    words = w.split()
    words = map(recapitalize_word, words)
    words = map(lambda w: w[0]+'.' if initial_re.match(w) else w, words)
    return ' '.join(words)


def recapitalize_word(w):
    """ Turns every fully capitalized word into an uncapitalized word (except for the first character) """
    if w.upper() == w:
        previousIsChar = False
        res = ''
        for i in range(len(w)):
            if previousIsChar:
                res += w[i].lower()
            else:
                res += w[i]
            previousIsChar = letter_re.match(w[i]) != None
        return res
    return w

def match_first_names(pair):
    a,b = pair
    if len(a) == 1 and len(b) > 0:
        return a.lower() == b[0].lower()
    elif len(b) == 1 and len(a) > 0:
        return b.lower() == a[0].lower()
    else:
        return a.lower() == b.lower()

def to_plain_name(name):
    return (name.first,name.last)

# Name normalization function used by the OAI proxy
nn_separator_re = re.compile(r',+ *')
nn_escaping_chars_re = re.compile(r'[\{\}\\]')
nn_nontext_re = re.compile(r'[^a-z_]+')
nn_final_nontext_re = re.compile(r'[^a-z_]+$')

def name_normalization(ident):
    ident = remove_diacritics(ident).lower()
    ident = ident.strip()
    ident = nn_separator_re.sub('_',ident)
    ident = nn_escaping_chars_re.sub('',ident)
    ident = nn_final_nontext_re.sub('',ident)
    ident = nn_nontext_re.sub('-',ident)
    return ident

def name_signature(first, last):
    ident = last.lower().strip()
    ident = nn_escaping_chars_re.sub('',ident)
    ident = nn_final_nontext_re.sub('',ident)
    ident = nn_nontext_re.sub('-',ident)
    if len(first):
        ident = first[0].lower()+'-'+ident
    return ident

#### Helpers for the name splitting heuristic ######

# Does this string contain a name initial?
def contains_initials(s):
    return initial_re.search(iunaccent(s)) != None
# Is this word fully capitalized?
def is_fully_capitalized(s):
    return lowercase_re.search(remove_diacritics(s)) == None
# Split a word according to a predicate
def predsplit_forward(predicate, words):
    first = []
    last = []
    predHolds = True
    for i in range(len(words)):
        if predicate(i) and predHolds:
            first.append(words[i])
        else:
            predHolds = False
            last.append(words[i])
    return (first,last)
# The same, but backwards
def predsplit_backwards(predicate, words):
    first = []
    last = []
    predHolds = True
    for i in reversed(range(len(words))):
        if predicate(i) and predHolds:
            last.insert(0, words[i])
        else:
            predHolds = False
            first.insert(0, words[i])
    return (first,last)


###### Name splitting heuristic based on name_tools ######

def parse_comma_name(name):
    """
    Parse a name of the form "Last name, First name" to (first name, last name)
    Try to do something reasonable if there is no comma.
    """
    if ',' in name:
        # In this case name_tools does it well
        prefix, first_name, last_name, suffix = name_tools.split(name)
    else:
        words = space_re.split(name)
        if not words:
            return ('','')
        first_name = None
        last_name = None
        from_lists = True

        # Search for initials in the words
        initial = map(contains_initials, words)
        capitalized = map(is_fully_capitalized, words)

        # CASE 1: the first word is capitalized but not all of them are
        # we assume that it is the first word of the last name
        if not initial[0] and capitalized[0] and not all(capitalized):
            (last,first) = predsplit_forward(
                    (lambda i: capitalized[i] and not initial[i]),
                    words)
            

        # CASE 2: the last word is capitalized but not all of them are
        # we assume that it is the last word of the last name
        elif not initial[-1] and capitalized[-1] and not all(capitalized):
            (first,last) = predsplit_forward(
                    (lambda i: (not capitalized[i]) or initial[i]),
                    words)

        # CASE 3: the first word is an initial
        elif initial[0]:
            (first,last) = predsplit_forward(
                    (lambda i: initial[i]),
                    words)

        # CASE 4: the last word is an initial
        # this is trickier, we know that the last name comes first
        # but we don't really know where it stops.
        # For simplicity we assume that all the words in the first
        # name are initials
        elif initial[-1]:
            (last,first) = predsplit_backwards(
                    (lambda i: initial[i]),
                    words)

        # CASE 5: there are initials in the name, but neither
        # at the beginning nor at the end
        elif True in initial:
            last_initial_idx = None
            for i in range(len(words)):
                if initial[i]:
                    last_initial_idx = i
            first = words[:last_initial_idx+1]
            last = words[last_initial_idx+1:]

        # CASE 6: we have no clue
        # We fall back on name_tools, where wise things are done
        # to parse correctly names such as "Colin de la Higuera"
        else:
            prefix, first_name, last_name, suffix = name_tools.split(name)
            from_lists = False
            
        if from_lists:
            first_name = ' '.join(first)
            last_name = ' '.join(last)

    first_name = first_name.strip()
    last_name = last_name.strip()
    first_name = normalize_name_words(first_name)
    last_name = normalize_name_words(last_name)

    if not last_name:
        first_name, last_name = last_name, first_name

    return (first_name,last_name)


