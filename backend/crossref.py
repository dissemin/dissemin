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

from urllib2 import URLError, HTTPError, build_opener
from urllib import urlencode
import json, requests
from requests.exceptions import RequestException
from unidecode import unidecode

from celery import current_task

from django.core.exceptions import ObjectDoesNotExist

from papers.errors import MetadataSourceException
from papers.doi import to_doi
from papers.name import match_names, normalize_name_words, parse_comma_name
from papers.utils import create_paper_fingerprint, iunaccent, tolerant_datestamp_to_datetime, date_from_dateparts, affiliation_is_greater, jpath, validate_orcid
from papers.models import Publication, Paper

from backend.utils import urlopen_retry
from backend.name_cache import name_lookup_cache
import backend.create

from dissemin.settings import DOI_PROXY_DOMAIN, DOI_PROXY_SUPPORTS_BATCH

######## HOW THIS MODULE WORKS ###########
#
# 1. Background on DOIs
#
# DOIs are managed by the DOI International Foundation. They provide
# a persistent identifier for objects. dx.doi.org redirects to the current
# URL for a given DOI (this URL can be updated by the provider).
#
# DOIs can be emitted by many different providers: among others, CrossRef,
# DataCite, MEDRA, etc.
#
# Using content negotiation, we can also retrieve metadata about these DOIs.
# By passing the header Accept: application/citeproc+json, supported by multiple
# academic DOI providers. This is *slow* because we need two HTTP requests per DOI
# to retrieve the metadata. Therefore we have implemented a proxy that caches
# this metadata and serves it in only one HTTP request once it is cached. It also
# provides a batch lookup capability.
#
# 2. CrossRef
#
# CrossRef is one particular DOI provider, the largest one for academic works.
# They provide their own search API that returns the metadata of the objects found.
# We do not need to use content negotation to fetch the metadata from CrossRef
# as it is already provided in the search results.
#
# Content negotiation remains useful for other providers (DOIs discovered by 
# other means).
#

# Number of results per page we ask the CrossRef search interface
# (looks like it does not support more than 20)
nb_results_per_request = 20
# Maximum timeout for the CrossRef interface (sometimes it is a bit lazy)
crossref_timeout = 15
# Maximum number of pages looked for a researcher
max_crossref_batches_per_researcher = 7
# Maximum number of non-trivially skipped records that do not match any researcher
crossref_max_skipped_records = 100


####### 1. Generic DOI metadata fetching tools ########

# Citeproc+json parsing utilities

def convert_to_name_pair(dct):
    """ Converts a dictionary {'family':'Last','given':'First'} to ('First','Last') """
    result = None
    if 'family' in dct and 'given' in dct:
        result = (dct['given'],dct['family'])
    elif 'family' in dct: # The 'Arvind' case
        result = ('',dct['family'])
    elif 'literal' in dct:
        result = parse_comma_name(dct['literal'])
    if result:
        result = (normalize_name_words(result[0]), normalize_name_words(result[1]))
    return result

def parse_crossref_date(date):
    """
    Parse the date representation from CrossRef to a python object
    """
    ret = None
    if 'date-parts' in date:
        try:
            for date in date['date-parts']:
                ret = date_from_dateparts(date)
                if ret is not None:
                    return ret
        except ValueError:
            pass
    if 'raw' in date:
        ret = tolerant_datestamp_to_datetime(date['raw']).date()
    return ret

def get_publication_date(metadata):
    """
    Get the publication date out of a record. If 'issued' is not present
    we default to 'deposited' although this might be quite inaccurate.
    But this case is rare anyway.
    """
    date = None
    if 'issued' in metadata:
        date = parse_crossref_date(metadata['issued'])
    if date is None and 'deposited' in metadata:
        date = parse_crossref_date(metadata['deposited'])
    return date

# Fetching utilities

def fetch_metadata_by_DOI(doi):
    """
    Fetch the metadata for a single DOI.
    This is supported by the standard proxy, dx.doi.org,
    as well as more advanced proxies such as doi_cache
    """
    addheaders = {'Accept':'application/citeproc+json'}
    try:
        request = 'http://'+DOI_PROXY_DOMAIN+'/'+doi
        response = urlopen_retry(request,
                timeout=crossref_timeout,
                headers=addheaders,
                retries=0)
        parsed = json.loads(response)
        return parsed
    except ValueError as e:
        raise MetadataSourceException('Error while fetching DOI metadata:\nInvalid JSON response.\n'+
                'Error: '+str(e))

def fetch_dois(doi_list):
    """
    Fetch the metadata of a list of DOIs from CrossRef,
    by batch if the server supports it, otherwise incrementally.
    """
    if DOI_PROXY_SUPPORTS_BATCH:
        return fetch_dois_by_batch(doi_list)
    else:
        return fetch_dois_incrementally(doi_list)

def fetch_dois_incrementally(doi_list):
    """
    Fetch a list of DOIs incrementally (useful when the proxy only supports this method
    or when we want to return the first metadata as soon as possible)
    """
    for doi in doi_list:
        try:
            metadata = fetch_metadata_by_DOI(doi)
        except MetadataSourceException as e:
            print "MetadataSourceException ignored:"
            print e
            continue
        yield metadata

def fetch_dois_by_batch(doi_list):
    """
    Fetch a list of DOIs by batch (useful when refreshing the list of publications
    of a given researcher, as the records have most likely been already cached before
    by the proxy)
    """
    if len(doi_list) == 0:
        return []
    data = {'dois':json.dumps(doi_list)}
    try:
        req = requests.post('http://'+DOI_PROXY_DOMAIN+'/batch', data)
        req.raise_for_status()
        return req.json()
    except RequestException as e:
        raise MetadataSourceException('Connecting to the DOI proxy at '+DOI_PROXY_DOMAIN+' failed: '+str(e))
    except ValueError as e:
        raise MetadataSourceException('Invalid JSON returned by the DOI proxy: '+str(e))
    except requests.exceptions.RequestException as e:
        raise MetadataSourceException('Failed to retrieve batch metadata from the proxy: '+str(e))

def save_doi_metadata(metadata, extra_affiliations=None):
    """
    Given the metadata as Citeproc+JSON or from CrossRef, create the associated paper and publication

    :param extra_affiliations: an optional affiliations list, which will be unified
        with the affiliations extracted from the metadata. This is useful for the ORCID interface.
    :returns: the paper, created if needed
    """        
    # Normalize metadata
    if metadata is None or type(metadata) != dict:
        if metadata is not None:
            print "WARNING: Invalid metadata: type is "+str(type(metadata))
            print "The doi proxy is doing something nasty!"
        raise ValueError('Invalid metadata format, expecting a dict')
    if not 'author' in metadata:
        raise ValueError('No author provided')

    if not 'title' in metadata or not metadata['title']:
        raise ValueError('No title')

    # the upstream function ensures that there is a non-empty title
    if not 'DOI' in metadata or not metadata['DOI']:
        raise ValueError("No DOI, skipping")
    doi = to_doi(metadata['DOI'])

    pubdate = get_publication_date(metadata)

    if pubdate is None:
        raise ValueError('No pubdate')
    
    title = metadata['title']
    # CrossRef metadata stores titles in lists
    if type(title) == list:
        title = title[0]
    authors = map(name_lookup_cache.lookup, map(convert_to_name_pair, metadata['author']))
    authors = filter(lambda x: x != None, authors)
    if all(not elem.is_known for elem in authors) or authors == []:
        raise ValueError('No known author')

    def get_affiliation(author_elem):
        # First, look for an ORCID id
        orcid = validate_orcid(author_elem.get('ORCID'))
        if orcid:
            return orcid
        # Otherwise return the plain affiliation, if any
        for dct in author_elem.get('affiliation', []):
            if 'name' in dct:
                return dct['name']

    affiliations = map(get_affiliation, metadata['author'])
    if extra_affiliations and len(affiliations) == len(extra_affiliations):
        for i in range(len(affiliations)):
            if affiliation_is_greater(extra_affiliations[i],affiliations[i]):
                affiliations[i] = extra_affiliations[i]

    print "Saved doi "+doi
    paper = backend.create.get_or_create_paper(title, authors, pubdate, 
            None, 'VISIBLE', affiliations)
    # The doi is not passed to this function so that it does not try to refetch the metadata
    # from CrossRef
    # create the publication, because it would re-fetch the metadata from CrossRef
    backend.create.create_publication(paper, metadata)
    return paper


##### CrossRef search API #######

def search_for_dois_incrementally(query, filters={}, max_batches=max_crossref_batches_per_researcher):
    """
    Searches for DOIs for the given query and yields their metadata as it finds them.

    :param query: the search query to pass to CrossRef
    :param filters: filters as specified by the REST API
    :param max_batches: maximum number of queries to send to CrossRef
    """
    params = {}
    if query:
        params['query'] = query
    if filters:
        params['filter'] = ','.join(map(lambda (k,v): k+":"+v, filters.items()))
    
    count = 0
    rows = 20
    offset = 0
    while not max_batches or count < max_batches:
        url = 'http://api.crossref.org/works'
        params['rows'] = rows
        params['offset'] = offset
        
        try:
            r = requests.get(url, params=params)
            print "CROSSREF: "+r.url
            js = r.json()
            for item in jpath('message/items', js, default=[]):
                yield item
        except ValueError as e:
            raise MetadataSourceException('Error while fetching CrossRef results:\nInvalid response.\n'+
                    'URL was: %s\nJSON parser error was: %s' % (request,unicode(e))) 
        except requests.exceptions.RequestException as e:
            raise MetadataSourceException('Error while fetching CrossRef results:\nUnable to open the URL: '+
                    request+'\nError was: '+str(e))

        offset += rows
        count += 1

def fetch_papers_from_crossref_by_researcher_name(name, update=False):
    """
    The update parameter forces the function to download again
    the metadata for DOIs that are already in the model
    """
    return search_for_dois_incrementally(unicode(name))


def fetch_publications(researcher, fetch_oai=True):
    """
    Fetch and save the publications from CrossRef for a given researcher

    :param fetch_oai: Try to fetch full text availability with proaixy.
    """
    # TODO: do it for all name variants of confidence 1.0
    researcher.status = 'Fetching DOI list.'
    researcher.save()
    nb_records = 0

    name = researcher.name
    lst = fetch_papers_from_crossref_by_researcher_name(name)

    count = 0
    skipped = 0
    for metadata in lst:
        if skipped > crossref_max_skipped_records:
            break

        try:
            yield save_doi_metadata(metadata)
        except ValueError:
            skipped += 1
            continue

        count += 1
        skipped = 0
    nb_records += count

    researcher.status = 'OK, %d records processed.' % nb_records
    researcher.save()

##### Zotero interface #####

def fetch_zotero_by_DOI(doi):
    """
    Fetch Zotero metadata for a given DOI.
    Works only with the doi_cache proxy.
    """
    try:
        request = requests.get('http://'+DOI_PROXY_DOMAIN+'/zotero/'+doi)
        return request.json()
    except ValueError as e:
        raise MetadataSourceException('Error while fetching Zotero metadata:\nInvalid JSON response.\n'+
                'Error: '+str(e))

def consolidate_publication(publi):
    """
    Fetches the abstract from Zotero and adds it to the publication if it succeeds.
    """
    zotero = fetch_zotero_by_DOI(publi.doi)
    if zotero is None:
        return publi
    for item in zotero:
        if 'abstractNote' in item:
            publi.abstract = item['abstractNote']
            publi.save(update_fields=['abstract'])
    return publi


