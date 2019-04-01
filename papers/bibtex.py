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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


import collections
import io
import re
import logging

import bibtexparser
import bibtexparser.customization

from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from papers.name import parse_comma_name

logger = logging.getLogger('dissemin.' + __name__)

# There should not be "et al" in Bibtex but we encounter it from time to time
ET_AL_RE = re.compile(r'( and )?\s*et\s+al\.?\s*$', re.IGNORECASE | re.UNICODE)
# Others is a reserved Bibtex keyword
OTHERS_RE = re.compile(r'( and )?\s*others\.?\s*$', re.IGNORECASE | re.UNICODE)

PAPER_TYPE_TO_BIBTEX = {
    'journal-article': 'article',
    'proceedings-article': 'inproceedings',
    'book-chapter': 'incollection',
    'book': 'book',
    'journal-issue': 'book',
    'proceedings': 'proceedings',
    'reference-entry': 'misc',
    'poster': 'misc',
    'report': 'article',
    'thesis': 'phdthesis',
    'dataset': 'misc',
    'preprint': 'article',
    'other': 'misc',
}


def parse_authors_list(record):
    """
    Split author field into a list of (First name, Last name)
    """
    if 'author' in record:
        if record['author']:
            # Handle "et al"
            record['author'] = ET_AL_RE.sub('', record['author'])
            # Handle "others"
            record['author'] = OTHERS_RE.sub('', record['author'])
            # Normalizations
            record['author'] = record['author'].replace('\n', ' ')
            # Split author field into list of first and last names
            record['author'] = [
                parse_comma_name(author.strip())
                for author in record['author'].split(' and ')
            ]
        else:
            del record['author']
    return record


def customizations(record):
    """
    Parser customizations for Bibtexparser
    """
    record = bibtexparser.customization.convert_to_unicode(record)
    record = parse_authors_list(record)
    return record


def parse_bibtex(bibtex):
    """
    Parse a single bibtex record represented as a string to a dict
    """
    parser = BibTexParser()
    parser.customization = customizations
    db = bibtexparser.loads(bibtex, parser=parser)

    if not db.entries:
        raise ValueError('No bibtex item was parsed.')
    if len(db.entries) > 1:
        logger.warning("%d bibtex items, defaulting to first one",
                       len(db.entries))

    return db.entries[0]


def format_paper_citation_dict(citation, indent='  '):
    """
    Format a citation dict for a paper or a list of papers into a BibTeX
    record string.

    :param citation: A ``Paper`` citation dict or list of such dicts.
    :param indent: Indentation to be used in BibTeX output.
    """
    if isinstance(citation, dict):
        entries = [citation]
    else:
        entries = citation

    # Handle conflicting ids for entries
    entries_ids = collections.defaultdict(lambda: 0)
    for entry in entries:
        entry_id = entry['ID']
        entries_ids[entry_id] += 1
        if entries_ids[entry_id] > 1:
            entry['ID'] = '%s_%s' % (entry_id, entries_ids[entry_id])

    writer = BibTexWriter()
    writer.indent = indent
    with io.StringIO('') as bibfile:
        db = BibDatabase()
        db.entries = entries
        bibfile.write(writer.write(db))
        return bibfile.getvalue().strip()
