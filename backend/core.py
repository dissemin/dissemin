# -*- coding: utf-8 -*-

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

from django.utils import timezone
import requests
import requests.exceptions
import json
from lxml import etree
from urllib import quote
from time import sleep
from datetime import date

import unicodedata
import itertools

from papers.errors import MetadataSourceException
from papers.models import *
from papers.name import parse_comma_name
from papers.utils import remove_diacritics

from backend.papersource import PaperSource
from backend.oai import my_oai_dc_reader
from backend.name_cache import name_lookup_cache

from dissemin.settings import CORE_API_KEY

core_timeout = 10
CORE_MAX_NO_MATCH_BEFORE_GIVE_UP = 30
CORE_BASE_URL = 'http://core.ac.uk/api-v2'
CORE_FETCH_METADATA_BATCH_SIZE = 100 # Max is 100
CORE_WAIT_TIME = 15 # seconds
CORE_RETRIES = 2 
CORE_WAIT_FACTOR = 2 # factor by which wait time is multiplied for subsequent retries

def query_core(url, params, post_payload=None, retries=CORE_RETRIES, wait_time=CORE_WAIT_TIME):
    """
    Generic function to send a request to CORE
    'url': local API URL, such as '/articles/search'
    'params': dict of GET parameters
    """
    if retries < 0:
        raise MetadataSourceException('Request to CORE failed: no retry left.\nURL was '+url)
    try:
        headers = {
                'apiKey':CORE_API_KEY,
                'user-agent':'dissem.in'
                }
        full_url = CORE_BASE_URL + url
        if post_payload is None:
            print "CORE GET request: "+full_url
            f = requests.get(full_url, params=params, headers=headers)
        else:
            print "CORE POST request: "+full_url
            f = requests.post(full_url, params=params,
                    data=json.dumps(post_payload), headers=headers)
        if f.status_code == 429:
            print "CORE Throttled, waiting for "+str(wait_time)+" sec"
            sleep(wait_timpe)
            query_core(url, params, post_payload, retries-1, CORE_WAIT_FACTOR*wait_time)
        elif f.status_code == 401:
            raise MetadataSourceException('Invalid CORE API key.')
        f.raise_for_status()
        parsed = f.json()
        return parsed
    except ValueError as e:
        raise MetadataSourceException('CORE returned invalid JSON payload for request '+full_url+'\n'+str(params)+'\n'+str(e))
    except requests.exceptions.RequestException as e:
        raise MetadataSourceException('HTTP error with CORE for URL: '+full_url+'\n'+str(params)+'\n'+str(e))

class CorePaperSource(PaperSource):
    """
    Fetches papers from the CORE search engine
    """
    def __init__(self, ccf):
        super(CorePaperSource, self).__init__(ccf)
        self.core_source, created =  OaiSource.objects.get_or_create(identifier='core',
                name='CORE',
                priority=0)

    def fetch_papers(self, researcher):
        name = researcher.name
        return self.fetch_by_name((name.first,name.last))

    def fetch_by_name(self, name, max_results=500):
        max_unsuccessful_lookups = CORE_MAX_NO_MATCH_BEFORE_GIVE_UP
        batch_size = CORE_FETCH_METADATA_BATCH_SIZE
        search_terms = 'authorsString:('+name[0]+' '+name[1]+')'
        ids = search_single_query(search_terms, max_results)
        
        unsuccessful_lookups = 0
        current_batch = list(itertools.islice(ids, batch_size))
        nb_results = 0
        while current_batch:
            results = fetch_paper_metadata_by_core_ids(current_batch)
            for result in results:
                match = None
                if result.get('status') == 'OK':
                    nb_results += 1
                    match = self.add_document(result)
                if match:
                    unsuccessful_lookups = 0
                    yield match
                else:
                    unsuccessful_lookups += 1
                if unsuccessful_lookups >= max_unsuccessful_lookups or nb_results >= max_results:
                    break
            if unsuccessful_lookups >= max_unsuccessful_lookups or nb_results >= max_results:
                break
            current_batch = list(itertools.islice(ids, batch_size))

    def add_document(self, doc):
        metadata = doc.get('data', {})
        authors_list = metadata.get('authors', [])
        if not authors_list:
            print "Ignoring CORE record as it has no creators."
            return False

        authors_list = map(parse_comma_name, authors_list)
        authors = map(name_lookup_cache.lookup, authors_list)
        
        # Filter the record
        if all(not elem.is_known for elem in authors):
            return False
        if not 'title' in metadata or not metadata['title']:
            return False
        title = metadata['title']

        print "########"
        print title
        print authors_list

        if not 'id' in metadata:
            print "WARNING: no CORE ID provided, skipping record"
            return False
        identifier = 'core:'+str(metadata['id'])
        splash_url = 'http://core.ac.uk/display/'+str(metadata['id'])
        pdf_urls = metadata.get('fulltextUrls', [])
        if 'fulltextIdentifier' in metadata:
            pdf_urls.append(metadata['fulltextIdentifier'])
        if metadata.get('hasFullText') == 'true' and pdf_urls == []:
            pdf_urls.append(splash_url)
        pdf_url = None
        if pdf_urls:
            pdf_url = pdf_urls[0]
        pubdate = None
        if 'year' in metadata:
            try:
                pubdate = date(year=int(metadata['year']),month=01,day=01)        
            except ValueError:
                pass
        doi = None # TODO parse the original record and look for DOIs
        #xml_record = list(doc.iter('metadata'))[0]
        #metadata = my_oai_dc_reader(xml_record)._map
        description = metadata.get('description')
        
        if pubdate is None or not title or not authors:
            return False

        paper = self.ccf.get_or_create_paper(title, authors, pubdate, doi, 'CANDIDATE')

        record = OaiRecord.new(
                about=paper,
                source=self.core_source,
                identifier=identifier,
                splash_url=splash_url,
                pdf_url=pdf_url,
                description=description,
                priority=self.core_source.priority)

        return paper

def search_single_query(search_terms, max_results=None, page_size=100):
    page = 1
    url = '/search/'+quote(remove_diacritics(search_terms))
    numSent = 0
    numTot = 0
    numYielded = 0
    while True:
        numResultsAskedFor = page_size
        if numTot:
            numResultsAskedFor = min(numTot-numSent,page_size)
        
        params = {
                'pageSize': str(numResultsAskedFor),
                'page': str(page),
            }
        res = query_core(url, params)
        numTot = res['totalHits']
        if res['status'] != 'OK':
            print "CORE: "+res['status']
            break
        for r in res['data']:
            if r.get('type') == 'article' and 'id' in r and numYielded < max_results:
                numYielded += 1
                yield int(r['id'])
            numSent += 1
        page += 1
        if numSent >= numTot or (max_results is not None and numYielded >= max_results) or len(res['data']) == 0:
            break
            


def fetch_paper_metadata_by_core_ids(core_ids):
    """
    Fetches CORE metadata for each CORE id provided,
    using the optimal combination of queries (hopefully).
    """
    batch_size = CORE_FETCH_METADATA_BATCH_SIZE
    batch = []
    for core_id in core_ids:
        if len(batch) < batch_size:
            batch.append(core_id)
        else:
            results = fetch_metadata_batch(batch)
            batch = []
            for r in results:
                yield r
    if len(batch) > 1:
        for r in fetch_metadata_batch(batch):
            yield r
    if len(batch) == 1:
        yield fetch_single_core_metadata(batch[0])

def fetch_metadata_batch(batch):
    """
    Fetches a batch of metadata from CORE in a single request
    """
    params = {
            'metadata':'true',
            'faithfulMetadata':'true',
            'fulltextUrls':'true',
            }
    response = query_core('/articles/get', params, batch)
    for item in response:
        yield item

def fetch_single_core_metadata(coreid):
    """
    Fetch a single article from its CORE id
    """
    params = {
            'metadata':'true',
            'faithfulMetadata':'true',
            'fulltextUrls':'true',
            }
    response = query_core('/articles/get/'+str(coreid), params)
    return response


