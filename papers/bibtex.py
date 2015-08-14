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

import re, bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from papers.name import parse_comma_name

def parse_bibtex(bibtex):
    """
    Parse a single bibtex record represented as a string to a dict
    """
    bibtex = insert_newlines_in_bibtex(bibtex)
    parser = BibTexParser()
    parser.customization = convert_to_unicode
    db = bibtexparser.loads(bibtex)#, parser=parser)

    if len(db.entries) == 0:
        raise ValueError('No bibtex item was parsed.')
    if len(db.entries) > 1:
        print "Warning: %d Bibtex items in parse_bibtex, defaulting to the first one" % len(db.entries)

    entry = db.entries[0]
    entry['author'] = parse_authors_list(entry.get('author', ''))
    return entry

### Bibtex utilites ###

bibtex_header_no_newline = re.compile(r'^(@\w*\W*{\W*\w+\W*,) *(?=[a-z])')
bibtex_statement_no_newline = re.compile(r'(},) *([a-zA-Z]+\W*=\W*{)')
bibtex_end_no_newline = re.compile(r'} *,? *} *$')

def insert_newlines_in_bibtex(bib):
    """
    Bibtexparser relies on newlines to parse bibtex records, and ORCiD does not provide
    them, so we need to insert them. This is probably plain wrong, but hey! I have
    no intension to write a full-blown bibtex parser.
    """
    bib1 = bibtex_header_no_newline.sub(r'\1\n', bib)
    bib2 = bibtex_statement_no_newline.sub(r'\1\n\2', bib1)
    bib3 = bibtex_end_no_newline.sub('}\n}', bib2)
    return bib3

def parse_authors_list(authors):
    return map(parse_comma_name, authors.split(' and '))

