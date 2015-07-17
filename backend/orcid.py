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

#import json, requests
#from requests.exceptions import RequestException
from unidecode import unidecode

from celery import current_task

from django.core.exceptions import ObjectDoesNotExist

from papers.errors import MetadataSourceException
from papers.doi import to_doi
from papers.name import match_names, normalize_name_words, parse_comma_name
from papers.utils import create_paper_fingerprint, iunaccent, tolerant_datestamp_to_datetime, date_from_dateparts, validate_orcid, parse_int
from papers.models import Publication, Paper, Name, OaiSource
from papers.bibtex import parse_bibtex

import backend.create
from backend.crossref import fetch_dois, save_doi_metadata
from backend.name_cache import name_lookup_cache

import requests, json
from datetime import date

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


orcid_type_to_pubtype = {
        'book':'book',
        'book-chapter':'book-chapter',
        'book-review':'other',
        'dictionary-entry':'reference-entry',
        'dissertation':'thesis',
        'encyclopedia-entry':'reference-entry',
        'edited-book':'book',
        'journal-article':'journal-article',
        'journal-issue':'journal-issue',
        'magazine-article':'other',
        'manual':'other',
        'online-resource':'dataset',
        'newsletter-article':'other',
        'newspaper-article':'other',
        'report':'report',
        'research-tool':'other',
        'supervised-student-publication':'other',
        'test':'other',
        'translation':'other',
        'website':'other',
        'working-paper':'preprint',
        'conference-abstract':'other',
        'conference-paper':'proceedings-article',
        'conference-poster':'poster',
        # Intellectual property section: skipped (-> 'other')
        'data-set':'dataset',
    }

def orcid_to_doctype(typ):
    return orcid_type_to_pubtype.get(typ.lower().replace('_','-').replace(' ','-'), 'other')
    

def jpath(path, js, default=None):
    def _walk(lst, js):
        if js is None:
            return default
        if lst == []:
            return js
        else:
            return _walk(lst[1:], js.get(lst[0],{} if len(lst) > 1 else default))
    return _walk(path.split('/'), js)

def fetch_orcid_records(id):
    """
    Queries ORCiD to retrieve the publications associated with a given ORCiD.
    """
    # Cleanup iD:
    id = validate_orcid(id)
    if id is None:
        raise MetadataSourceException('Invalid ORCiD identifier')

    # Get ORCiD profile
    try:
        headers = {'Accept':'application/orcid+json'}
        profile_req = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % id, headers=headers)
        profile = profile_req.json()
    except requests.exceptions.HTTPError:
        raise MetadataSourceException('The ORCiD %s could not be found' % id)
    except ValueError as e:
        raise MetadataSourceException('The ORCiD %s returned invalid JSON.' % id)

    # curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0002-8612-8827/orcid-works' -L -i
    dois = []

    # Fetch publications
    pubs = jpath('orcid-profile/orcid-activities/orcid-works/orcid-work', profile)
    for pub in pubs:
        def j(path, default=None):
            return jpath(path, pub, default)

        # DOI
        doi = None
        for extid in j('work-external-identifiers/work-external-identifier', []):
            if extid.get('work-external-identifier-type') == 'DOI':
                doi = to_doi(jpath('work-external-identifier-id/value', extid))
        if doi:
            # If a DOI is available, create the paper using metadata from CrossRef.
            # We don't do it yet, we only store the DOI, so that we can fetch them
            # by batch later.
            dois.append(doi)
            continue

        # Otherwise, extract information from ORCiD

        # Title
        title = j('work-title/title/value')
        if title is None:
            print "Warning: Skipping ORCID publication: no title"
        
        # Type
        doctype = orcid_to_doctype(j('work-type', 'other'))

        # Bibtex
        bibtex = None
        if j('work-citation/work-citation-type') == 'BIBTEX':
            bibtex = j('work-citation/citation')

        # Contributors (ignored for now as they are very often not present)
        #def get_contrib(js):
        #    return {
        #        'orcid':jpath('contributor-orcid', js),
        #        'name': jpath('credit-name/value', js),
        #        }
        #authors = map(get_contrib, j('work-contributors/contributor',[]))

        # Parse bibtex
        if bibtex is None:
            print "Warning: Skipping ORCID publication: no contributors or Bibtex."
            print j('work-citation/work-citation-type')
            continue
        entry = parse_bibtex(bibtex)

        authors = map(name_lookup_cache.lookup, entry['author'])

        # Pubdate
        year = parse_int(j('publication-date/year/value'), 1970)
        month = parse_int(j('publication-date/month/value'), 01)
        day = parse_int(j('publication-date/day/value'), 01)
        pubdate = date(year=year, month=month, day=day)

        # ORCiD internal id
        identifier = j('put-code')

        # Create paper:
        paper = backend.create.get_or_create_paper(title, authors, pubdate)
        record = backend.create.create_oairecord(
                source=orcid_oai_source,
                identifier=identifier,
                about=paper,
                splash_url='http://orcid.org/'+id,
                pubtype=doctype)

    doi_metadata = fetch_dois(dois)
    for metadata in doi_metadata:
        try:
            save_doi_metadata(metadata)
        except ValueError:
            pass

orcid_oai_source, _ = OaiSource.objects.get_or_create(identifier='orcid',
            defaults={'name':'ORCiD','oa':False,'priority':1,'default_pubtype':'misc'})
