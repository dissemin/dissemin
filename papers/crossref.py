# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from urllib2 import urlopen, URLError, HTTPError, build_opener
from urllib import urlencode
import json

from celery import current_task

from papers.errors import MetadataSourceException
from papers.doi import to_doi
from papers.utils import match_names, normalize_name_words
from papers.models import DoiRecord

nb_results_per_request = 25
crossref_timeout = 5

def fetch_list_of_DOIs_from_crossref(query, page, number):
    try:
        page = int(page)
        number = int(number)
    except ValueError:
        raise ValueError("Page and number have to be integers.")

    query_args = {'q':query, 'page':str(page), 'number':str(number)}
    request = 'http://search.crossref.org/dois?'+urlencode(query_args)
    try:
        f = urlopen(request, timeout=crossref_timeout)
        response = f.read()
        parsed = json.loads(response)
        result = []
        for dct in parsed:
            if 'doi' in dct:
                parsed = to_doi(dct['doi'])
                if parsed:
                    result.append(parsed)
        return result
    except ValueError as e:
        raise MetadataSourceException('Error while fetching metadata:\nInvalid response.\n'+
                'URL was: %s\nJSON parser error was: %s' % (request,unicode(e))) 
    except URLError as e:
        raise MetadataSourceException('Error while fetching metadata:\nUnable to open the URL: '+
                request+'\nError was: '+str(e))

def fetch_metadata_by_DOI(doi):
    opener = build_opener()
    opener.addheaders = [('Accept','application/citeproc+json')]
    try:
        request = 'http://dx.doi.org/'+doi
        response = opener.open(request).read() # TODO is this unsecure ?
        parsed = json.loads(response)
        return parsed
    except HTTPError as e:
        if e.code == 404:
            return None
        raise MetadataSourceException('Error while fetching DOI metadata:\nUnable to open the URL: '+
                request+'\nError was: '+str(e))
    except URLError as e:
        raise MetadataSourceException('Error while fetching DOI metadata:\nUnable to open the URL: '+
                request+'\nError was: '+str(e))
    except ValueError as e:
        raise MetadataSourceException('Error while fetching DOI metadata:\nInvalid JSON response.\n'+
                'Error: '+str(e))

def save_doi_record(parsed_doi_metadata, paper):
    metadata = parsed_doi_metadata

    doi = to_doi(metadata['doi'])
    matches = DoiRecord.objects.filter(doi__exact = doi)
    if matches:
        rec = matches[0]
        # TODO if the current paper is different from the argument
        # TODO MERGE THE TWO
    else:
        rec = DoiRecord(doi=doi, about=paper)
        rec.save()


def convert_to_name_pair(dct):
    """ Converts a dictionary {'family':'Last','given':'First'} to ('First','Last') """
    result = None
    if 'family' in dct and 'given' in dct:
        result = (dct['given'],dct['family'])
    elif 'family' in dct: # The 'Arvind' case
        result = ('',dct['family'])
    if result:
        result = (normalize_name_words(result[0]), normalize_name_words(result[1]))
    return result

def fetch_papers_from_crossref_by_researcher_name(name):
    researcher_found = True
    batch_number = 1
    results = []

    # The search term sent to CrossRef is the name of the researcher
    query = unicode(name)

    # While a valid resource where the researcher is author or editor is found
    count = 0
    while researcher_found:
        researcher_found = False

        # Get the next batch of DOIs
        dois = fetch_list_of_DOIs_from_crossref(query, batch_number, nb_results_per_request)
        batch_number += 1

        for doi in dois:
            print "Fetching DOI "+doi
            metadata = fetch_metadata_by_DOI(doi)
            if metadata == None:
                continue
            if not 'author' in metadata: # TODO handle journals: not author but editor
                continue
            authors = map(convert_to_name_pair, metadata['author'])

            for a in authors:
                print a[0]+' '+a[1]
            matching_authors = filter(lambda a: match_names(a,(name.first,name.last)), authors)
            if not matching_authors:
                continue
            print "Saved."
            researcher_found = True
            results.append(metadata)

            count += 1
            if count % 10 == 0:
                current_task.update_state('FETCHING', meta={'nbRecords':count})

    return results

