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
from papers.utils import create_paper_fingerprint, iunaccent, tolerant_datestamp_to_datetime, date_from_dateparts
from papers.models import Publication, Paper

from backend.utils import urlopen_retry
from backend.name_cache import name_lookup_cache
import backend.create

from dissemin.settings import DOI_PROXY_DOMAIN, DOI_PROXY_SUPPORTS_BATCH

# Number of results per page we ask the CrossRef search interface
# (looks like it does not support more than 20)
nb_results_per_request = 20
# Maximum timeout for the CrossRef interface (sometimes it is a bit lazy)
crossref_timeout = 15
# Maximum number of pages looked for a researcher
max_crossref_batches_per_researcher = 25
# Maxmimum number of batches trivially skipped (because the last name does not occur in them)
crossref_max_empty_batches = 5
# Maximum number of non-trivially skipped records that do not match any researcher
crossref_max_skipped_records = 100


def fetch_list_of_DOIs_from_crossref(query, page, number, citationToken=None):
    """
    Queries the search interface and returns a list of potentially relevant DOIs.
    This does not return the full metadata, only the DOI lists.
    - query is the string to search for (the CrossRef query)
    - number is the number of records to display on each page (apparently only 20 works)
    - page is the page number (starting at 0)
    - citationToken is a token to look for in the full citation. If it is not present,
      the DOI will not be returned. Concretely, this is used with the last name of the
      researcher we look at, because there are no chances that the paper will make
      it through the rest of the pipeline if the last name does not occur exactly 
      in this form.
    """
    try:
        page = int(page)
        number = int(number)
    except ValueError:
        raise ValueError("Page and number have to be integers.")

    if citationToken:
        citationToken = iunaccent(citationToken)

    query_args = {'q':unidecode(query), 'page':str(page), 'number':str(number)}
    request = 'http://search.crossref.org/dois?'+urlencode(query_args)
    try:
        response = urlopen_retry(request, timeout=crossref_timeout)
        parsed = json.loads(response)
        result = []
        for dct in parsed:
            if citationToken and not ('fullCitation' in dct and
                    citationToken in iunaccent(dct['fullCitation'])):
                continue
            if 'doi' in dct and 'title' in dct:
                parsed = to_doi(dct['doi'])
                if parsed and dct['title']:
                    result.append(parsed)
        return result
    except ValueError as e:
        raise MetadataSourceException('Error while fetching metadata:\nInvalid response.\n'+
                'URL was: %s\nJSON parser error was: %s' % (request,unicode(e))) 
    except MetadataSourceException as e:
        raise MetadataSourceException('Error while fetching metadata:\nUnable to open the URL: '+
                request+'\nError was: '+str(e))

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

def fetch_papers_from_crossref_by_researcher_name(name, update=False):
    """
    The update parameter forces the function to download again
    the metadata for DOIs that are already in the model
    """
    researcher_found = True
    batch_number = 1
    results = []

    # The search term sent to CrossRef is the name of the researcher
    query = unicode(name)

    # While a valid resource where the researcher is author or editor is found
    count = 0
    empty_batches = 0
    while (batch_number < max_crossref_batches_per_researcher and
            empty_batches < crossref_max_empty_batches):
        print ""
        print "Batch number "+str(batch_number)

        # Get the next batch of DOIs
        dois = fetch_list_of_DOIs_from_crossref(query, batch_number, nb_results_per_request, name.last)
        batch_number += 1
        if len(dois) == 0:
            empty_batches += 1

        records = { publi.doi:publi for publi in Publication.objects.filter(doi__in=dois) }
        if update:
            for r in records:
                yield records
        count += len(records)
        missing_dois = []
        for doi in dois:
            if doi not in records:
                missing_dois.append(doi)
        print "%d dois. %d records already present, fetching %d new ones" % (len(dois), len(records), len(missing_dois))

        if DOI_PROXY_SUPPORTS_BATCH:
            new_dois = fetch_dois_by_batch(missing_dois)
        else:
            new_dois = fetch_dois_incrementally(missing_dois)
            
        for metadata in new_dois:
               # Normalize metadata
            if metadata is None or type(metadata) != type({}):
                if metadata is not None:
                    print "WARNING: Invalid metadata: type is "+str(type(metadata))
                    print "The doi proxy is doing something nasty!"
                continue
            if not 'author' in metadata:
                continue

            if not 'title' in metadata or not metadata['title']:
                print "No title, skipping"
                continue 

            # Save it!
            yield metadata

            count += 1
            if count % 10 == 0 and hasattr(current_task, 'update_state'):
                current_task.update_state('FETCHING', meta={'nbRecords':count})

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
            

def fetch_publications(researcher):
    """
    Fetch and save the publications from CrossRef for a given researcher
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

        # the upstream function ensures that there is a non-empty title
        if not 'DOI' in metadata or not metadata['DOI']:
            print "No DOI, skipping"
            skipped += 1
            continue
        doi = to_doi(metadata['DOI'])

        pubdate = get_publication_date(metadata)

        if pubdate is None:
            print "No pubdate, skipping"
            skipped += 1
            continue
        
        title = metadata['title']
        authors = map(name_lookup_cache.lookup, map(convert_to_name_pair, metadata['author']))
        authors = filter(lambda x: x != None, authors)
        if all(not elem.is_known for elem in authors) or authors == []:
            skipped += 1
            continue
        print "Saved doi "+doi
        paper = backend.create.get_or_create_paper(title, authors, pubdate) # don't let this function
        # create the publication, because it would re-fetch the metadata from CrossRef
        backend.create.create_publication(paper, metadata)

        count += 1
        skipped = 0
    nb_records += count

    researcher.status = 'OK, %d records processed.' % nb_records
    researcher.save()



