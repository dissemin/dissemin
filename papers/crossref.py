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
import json

from celery import current_task
from django.core.exceptions import ObjectDoesNotExist

from papers.errors import MetadataSourceException
from papers.doi import to_doi
from papers.utils import match_names, normalize_name_words, create_paper_fingerprint, urlopen_retry, iunaccent
from papers.models import Publication, Paper

from unidecode import unidecode

nb_results_per_request = 30
crossref_timeout = 5
max_crossref_batches_per_researcher = 40

def fetch_list_of_DOIs_from_crossref(query, page, number, citationToken=None):
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
        f = urlopen_retry(request, timeout=crossref_timeout)
        response = f.read()
        parsed = json.loads(response)
        result = []
        for dct in parsed:
            if citationToken and not ('fullCitation' in dct and citationToken in iunaccent(dct['fullCitation'])):
                continue
            if 'doi' in dct and 'title' in dct:
                parsed = to_doi(dct['doi'])
                if parsed and dct['title']:
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
        response = urlopen_retry(request, opener=opener).read() 
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
    while researcher_found and batch_number < max_crossref_batches_per_researcher:
        researcher_found = False

        # Get the next batch of DOIs
        dois = fetch_list_of_DOIs_from_crossref(query, batch_number, nb_results_per_request, name.last)
        batch_number += 1

        for doi in dois:
            # First check whether the DOI is already in the model
            if not update:
                try:
                    Publication.objects.get(doi=doi)
                    print "Skipped as it is already in the model"
                    researcher_found = True
                    continue # The DOI already exists, skipping
                except ObjectDoesNotExist:
                    pass

            # Fetch DOI details from CrossRef
            print "Fetching DOI "+doi
            try:
                metadata = fetch_metadata_by_DOI(doi)
            except MetadataSourceException as e:
                print "MetadataSourceException ignored:"
                print e
                continue

            # Normalize metadata
            if metadata == None:
                continue
            if not 'author' in metadata:
                continue
            authors = map(convert_to_name_pair, metadata['author'])
            if not 'title' in metadata or not metadata['title']:
                print "No title, skipping"
                continue 

            save_doi = False
            
            # First look if the paper is already known.
            # This is useful because we might have got the full names of the authors
            # from another source (e.g. OAI) but we might have only the initials
            # in the CrossRef version. If the fingerprints match, we can magically
            # expand the initials and associate the DOI to the initial paper.
            fp = create_paper_fingerprint(metadata['title'], authors)
            try:
                Paper.objects.get(fingerprint=fp)
                # If the paper is already found, then the DOI is relevant: we emit it.
                print "Matching paper found"
                save_doi = True
            except ObjectDoesNotExist:
                # Otherwise we might not have heard of it before, but it might be
                # still relevant (i.e. involving one of the known researchers)
                pass

            # Then look if any of the authors is known
            for a in authors:
                if a:
                    print a[0]+' '+a[1]
            if not save_doi:
                matching_authors = filter(lambda a: match_names(a,(name.first,name.last)), authors)

                # If one of them matches the target name, we save it
                if matching_authors:
                    save_doi = True

            if not save_doi:
                continue

            # Otherwise we save it!
            researcher_found = True
            print "Saved."
            yield metadata

            count += 1
            if count % 10 == 0:
                current_task.update_state('FETCHING', meta={'nbRecords':count})

