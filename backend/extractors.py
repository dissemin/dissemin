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



import re
from papers.doi import to_doi
from backend.doiprefixes import free_doi_prefixes

class URLExtractor(object):

    def __init__(self):
        """
        Init the extractor, usually with some parameters
        """

    def extract(self, header, metadata):
        """
        Take a record (header + metadata) and return a dict()
        containing some keys among ['pdf', 'splash'] and
        whose values are respectively the PDF URL and splash URL
        """
        self.header = header
        self.metadata = metadata
        return self._post_filter(self._urls())

    def _urls(self):
        """
        Does the actual extraction job.
        """
        return dict()

    def _post_filter(self, urls):
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

    def _urls(self):

        urls = dict()
        for (field, regex, resource_type, skeleton) in self.mappings:
            for val in self.metadata[field]:
                val = val.strip()
                match = regex.match(val)
                if match:
                    urls[resource_type] = regex.sub(skeleton, val)
        return urls


class CairnExtractor(RegexExtractor):

    def __init__(self, mappings):
        super(CairnExtractor, self).__init__(mappings)

    def _post_filter(self, urls):
        if not 'free access' in self.metadata.get('accessRights'):
            urls['pdf'] = None
        return urls


class OpenAireExtractor(RegexExtractor):

    def __init__(self, mappings):
        super(OpenAireExtractor, self).__init__(mappings)

    def _post_filter(self, urls):
        if 'info:eu-repo/semantics/openAccess' in self.metadata.get('rights', []):
            urls['pdf'] = urls.get('splash')
        return urls


pmc_id_re = re.compile(r'ftpubmed:oai:pubmedcentral\.nih\.gov:([0-9]*)')
pmc_url_re = re.compile(r'https?://www\.ncbi\.nlm\.nih\.gov/pmc/articles/PMC\d+')
pmid_url_re = re.compile(r'https?://www\.ncbi\.nlm\.nih\.gov/pubmed/\d+')

class BaseExtractor(RegexExtractor):

    def __init__(self, mappings):
        super(BaseExtractor, self).__init__(mappings)

    def _post_filter(self, urls):
        if '1' in self.metadata.get('oa', []):
            urls['pdf'] = urls.get('splash')

        # Special case for PMC as their metadata includes other urls
        pmc_match = pmc_id_re.match(self.header.identifier())
        if pmc_match:
            pmc_url = None
            for u in self.metadata.get('identifier',[]):
                # rationale : PMC urls are prioritary
                # but PMID urls can be used when no PMC url is provided
                # (because we know they link to PMC eventually, from the
                # identifier)
                if pmc_url_re.match(u) or (not pmc_url and pmid_url_re.match(u)):
                    pmc_url = u

            urls['splash'] = pmc_url
            urls['pdf'] = pmc_url

        # Special case for DOIs
        if urls.get('splash'):
            doi = to_doi(urls.get('splash'))
            if doi:
                doi_prefix = doi.split('/')[0]
                if doi_prefix in free_doi_prefixes:
                    urls['pdf'] = urls['splash']

        return urls

arxivExtractor = RegexExtractor([
    ('identifier', re.compile(r'(http://arxiv.org/abs/[^ ]*)$'),
        'splash', r'\1'),
    ('identifier', re.compile(r'http://arxiv.org/abs/([^ ]*)$'),
        'pdf', r'http://arxiv.org/pdf/\1')
    ])

halExtractor = RegexExtractor([
    ('identifier', re.compile(r'(https?://[a-z\-0-9.]*/[a-z0-9\-]*)$'),
        'splash', r'\1'),
    ('identifier', re.compile(r'(https?://[a-z\-0-9.]*/[a-z0-9\-]*/document)$'),
        'pdf', r'\1'),
    ])

cairnExtractor = CairnExtractor([
    ('identifier', re.compile(r'(http://www\.cairn\.info/article\.php\?ID_ARTICLE=[^ ]*)$'),
        'splash', r'\1'),
    ('identifier', re.compile(r'(http://www\.cairn\.info/)article(\.php\?ID_ARTICLE=[^ ]*)$'),
        'pdf', r'\1load_pdf\2'),
    ])

pmcExtractor = RegexExtractor([
    ('identifier', re.compile(r'(https?://www\.ncbi\.nlm\.nih\.gov/pubmed/[0-9]+)$'),
        'splash', r'\1'),
    ('identifier', re.compile(r'https?://www\.ncbi\.nlm\.nih\.gov/pubmed/([0-9]+)$'),
        'pdf', r'http://www.ncbi.nlm.nih.gov/pmc/articles/pmid/\1'),
    ('identifier', re.compile(r'.*/pmc/articles/PMC(\d+)/$'),
        'splash', r'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC\1/'),
    ('identifier', re.compile(r'.*/pmc/articles/PMC(\d+)/$'),
        'pdf', r'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC\1/'),
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

researchgateExtractor = RegexExtractor([
    ('source', re.compile(r'(https?://[^ ]*)'),
        'splash', r'\1'),
    ('identifier', re.compile(r'(https?://[^ ]*\.pdf)'),
        'pdf', r'\1'),
        ])

baseExtractor = BaseExtractor([
    ('identifier', re.compile(r'(https?://.*)'), 'splash', r'\1'),
    ('identifier', re.compile(r'(https?://.*\.pdf)'), 'pdf', r'\1'),
    ('link', re.compile(r'(https?://.*)'), 'splash', r'\1'),
    ('link', re.compile(r'(https?://.*\.pdf)'), 'pdf', r'\1'),
    ])

defaultExtractor = RegexExtractor([
    ('source', re.compile(r'(https?://[^ ]*)'),
        'splash', r'\1')])

REGISTERED_OAI_EXTRACTORS = {
        'arxiv': arxivExtractor,
        'hal': halExtractor,
        'cairn': cairnExtractor,
        'pmc': pmcExtractor,
        'doaj': doajExtractor,
        'persee': perseeExtractor,
        'numdam': numdamExtractor,
        'zenodo': zenodoExtractor,
        'base': baseExtractor,
        'researchgate': researchgateExtractor,
        }
