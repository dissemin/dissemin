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

from papers.models import OaiSource

import re
import os

class URLExtractor(object):
    def __init__(self):
        """
        Init the extractor, usually with some parameters
        """
        pass

    def extract(self, record):
        """
        Take a record (header + metadata) and return a dict()
        containing some keys among ['pdf', 'splash'] and
        whose values are respectively the PDF URL and splash URL
        """
        return self._post_filter(record, self._urls(record))

    def _urls(self, record):
        """
        Does the actual extraction job.
        """
        return dict()

    def _post_filter(self, record, urls):
        """
        Filters the URLs according to the record.
        Reimplement if you want to filter the results of a predefined filter.
        """
        return urls


class RegexExtractor(URLExtractor):
    def __init__(self, mappings):
        """
        mappings: list of (field,regex,resource_type,skeleton)
        """
        super(RegexExtractor, self).__init__()
        self.mappings = mappings

    def _urls(self, record):
        metadata = record[1]._map

        urls = dict()
        for (field,regex,resource_type,skeleton) in self.mappings:
            for val in metadata[field]:
                val = val.strip()
                match = regex.match(val)
                if match:
                    urls[resource_type] = regex.sub(skeleton, val)
        return urls

class CairnExtractor(RegexExtractor):
    def __init__(self, mappings):
        super(CairnExtractor, self).__init__(mappings)

    def _post_filter(self, record, urls):
        if not 'free access' in record[1]._map.get('accessRights'):
            urls['pdf'] = None
        return urls

class OpenAireExtractor(RegexExtractor):
    def __init__(self, mappings):
        super(OpenAireExtractor, self).__init__(mappings)

    def _post_filter(self, record, urls):
        if 'info:eu-repo/semantics/openAccess' in record[1]._map.get('rights', []):
            urls['pdf'] = urls.get('splash')
        return urls

class BaseExtractor(RegexExtractor):
    def __init__(self, mappings):
        super(BaseExtractor, self).__init__(mappings)

    def _post_filter(self, record, urls):
        if '2' in record[1]._map.get('oa', []):
            urls['pdf'] = urls.get('splash')
        return urls

arxivExtractor = RegexExtractor([
    ('identifier',re.compile(r'(http://arxiv.org/abs/[^ ]*)$'),
        'splash',r'\1'),
    ('identifier',re.compile(r'http://arxiv.org/abs/([^ ]*)$'),
        'pdf',r'http://arxiv.org/pdf/\1')
    ])

halExtractor = RegexExtractor([
    ('identifier',re.compile(r'(https?://[a-z\-0-9.]*/[a-z0-9\-]*)$'),
        'splash', r'\1'),
    ('identifier',re.compile(r'(https?://[a-z\-0-9.]*/[a-z0-9\-]*/document)$'),
        'pdf', r'\1'),
    ])

cairnExtractor = CairnExtractor([
    ('identifier',re.compile(r'(http://www\.cairn\.info/article\.php\?ID_ARTICLE=[^ ]*)$'),
        'splash',r'\1'),
    ('identifier',re.compile(r'(http://www\.cairn\.info/)article(\.php\?ID_ARTICLE=[^ ]*)$'),
        'pdf',r'\1load_pdf\2'),
    ])

pmcExtractor = RegexExtractor([
    ('identifier', re.compile(r'(https?://www\.ncbi\.nlm\.nih\.gov/pubmed/[0-9]+)$'),
        'splash', r'\1'),
    ('identifier', re.compile(r'https?://www\.ncbi\.nlm\.nih\.gov/pubmed/([0-9]+)$'),
        'pdf', r'http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/\1')
    ])

doajExtractor = RegexExtractor([
    ('relation', re.compile(r'(https?://[^ ]*)'),
        'pdf', r'\1'),
    ('identifier', re.compile(r'(http://doaj\.org/search[^ ]*)'),
        'splash', r'\1'),
    ('identifier', re.compile(r'(https?://doaj\.org/article/[^ ]*)'),
        'splash', r'\1'),
    ])

perseeExtractor = RegexExtractor([
    ('identifier', re.compile(r'(http://www\.persee\.fr/web/revues/home/[^ ]*)'),
        'splash', r'\1'),
    ('identifier', re.compile(r'(http://www\.persee\.fr/web/revues/home/[^ ]*)'),
        'pdf', r'\1'),
    ])

numdamExtractor = RegexExtractor([
    ('identifier', re.compile(r'(http://www\.numdam\.org/item\?id=[^ ]*)'),
        'splash', r'\1'),
    ('identifier', re.compile(r'http://www\.numdam\.org/item\?id=([^ ]*)'),
        'pdf', r'http://archive.numdam.org/article/\1.pdf'),
    ])

zenodoExtractor = OpenAireExtractor([
    ('identifier', re.compile(r'(https?://zenodo.org/record/[0-9]*)'),
        'splash', r'\1'),
    ])

baseExtractor = BaseExtractor([
    ('identifier', re.compile(r'(http://.*)'), 'splash', r'\1'),
    ('identifier', re.compile(r'(http://.*\.pdf)'), 'pdf', r'\1'),
    ('link', re.compile(r'(http://.*)'), 'splash', r'\1'),
    ('link', re.compile(r'(http://.*\.pdf)'), 'pdf', r'\1'),
    ])


REGISTERED_EXTRACTORS = {
        'arxiv': arxivExtractor,
        'hal': halExtractor,
        'cairn' : cairnExtractor,
        'pmc' : pmcExtractor,
        'doaj' : doajExtractor,
        'persee' : perseeExtractor,
        'numdam' : numdamExtractor,
        'zenodo': zenodoExtractor,
        'base' : baseExtractor,
        }

# Set up the model for the sources
oai_sources = [
        ('arxiv','arXiv',False, 10,'preprint'),
        ('hal', 'HAL', False, 10, 'preprint'),
        ('cairn', 'Cairn', False, 10, 'preprint'),
        ('pmc', 'PubMed Central', False, 10, 'preprint'),
        ('doaj', 'DOAJ', True, 10, 'journal-article'),
        ('persee', 'Persée', True, 10, 'preprint'),
        ('zenodo', 'Zenodo', False, 15, 'preprint'),
        ('numdam', 'Numdam', False, 10, 'journal-article'),
        ('base', 'BASE', False, -2, 'preprint'),
        ]

if os.environ.get('READTHEDOCS', None) != 'True':

    # Auto-create all the Oai Sources when this module is imported
    for identifier, name, oa, priority, pubtype in oai_sources:
        OaiSource.objects.get_or_create(identifier=identifier,
                defaults={'name':name,'oa':oa,'priority':priority,'default_pubtype':pubtype})



