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

from papers.utils import normalize_name_words, iunaccent, remove_diacritics

# Name managemement: heuristics to separate a name into (first,last)
comma_re = re.compile(r',+')
space_re = re.compile(r'\s+')
initial_re = re.compile(r'(^|\W)\w(\W|$)')
lowercase_re = re.compile(r'[a-z]')

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

def parse_comma_name(name):
    """
    Parse an name of the form "Last name, First name" to (first name, last name)
    Tries to do something reasonable if there is no comma.
    """
    if ',' in name:
        name = comma_re.sub(',',name)
        idx = name.find(',')
        last_name = name[:idx]
        first_name = name[(idx+1):]
    else:
        # TODO: there is probably a better way to parse names such as "Colin de la Higuera"
        # list of "particle words" such as "de, von, van, du" ?
        # That would be europe-centric though...
        words = space_re.split(name)
        if not words:
            return ('','')

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
            (first,last) = predsplit_backwards(
                    (lambda i: capitalized[i] and not initial[i]),
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
        # We simply cut roughly in the middle !
        else:
            cut_idx = len(words)/2
            if len(words) == 3:
                cut_idx = 2
            first = words[:cut_idx]
            last = words[cut_idx:]
            
        first_name = ' '.join(first)
        last_name = ' '.join(last)

    first_name = first_name.strip()
    last_name = last_name.strip()
    first_name = normalize_name_words(first_name)
    last_name = normalize_name_words(last_name)

    if not last_name:
        first_name, last_name = last_name, first_name

    return (first_name,last_name)


