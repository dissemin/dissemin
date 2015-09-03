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
from papers.name import match_names, normalize_name_words, parse_comma_name, shallower_name_similarity
from papers.utils import create_paper_fingerprint, iunaccent, tolerant_datestamp_to_datetime, date_from_dateparts, validate_orcid, parse_int
from papers.models import Publication, Paper, Name, OaiSource, OaiRecord
from papers.bibtex import parse_bibtex
from papers.orcid import *

import backend.create
from backend.crossref import fetch_dois, save_doi_metadata, convert_to_name_pair
from backend.name_cache import name_lookup_cache


import requests, json
from datetime import date

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
    

def affiliate_author_with_orcid(ref_name, orcid, authors, initial_affiliations=None):
    """
    Given a reference name and an ORCiD for a researcher, find out which
    author in the list is the most likely to be that author. This function
    is run on author lists of papers listed in the ORCiD record so we expect
    that one of the authors should be the same person as the ORCiD holder.
    This just finds the most similar name and returns the appropriate affiliations
    list (None everywhere except for the most similar name where it is the ORCiD).
    """
    max_sim_idx = None
    max_sim = 0.
    for idx, name in enumerate(authors):
        cur_similarity = shallower_name_similarity(name, ref_name) 
        if cur_similarity > max_sim:
            max_sim_idx = idx
            max_sim = cur_similarity
    affiliations = initial_affiliations or [None]*len(authors)
    if max_sim_idx is not None:
        affiliations[max_sim_idx] = orcid
    return affiliations

def fetch_orcid_records(id, profile=None, use_doi=True):
    """
    Queries ORCiD to retrieve the publications associated with a given ORCiD.

    :param profile: The ORCID profile if it has already been fetched before (format: parsed JSON).
    :param use_doi: Fetch the publications by DOI when we find one (recommended, but slow)
    :returns: the number of records we managed to extract from the ORCID profile (some of them could be in
            free form, hence not imported)
    """
    # Cleanup iD:
    id = validate_orcid(id)
    if id is None:
        raise MetadataSourceException('Invalid ORCiD identifier')

    # Get ORCiD profile
    try:
        if profile is None:
            profile = OrcidProfile(id=id)
        else:
            profile = OrcidProfile(json=profile)
    except MetadataSourceException as e:
        print e
        return 0

    # Reference name
    ref_name = profile.name
    # curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0002-8612-8827/orcid-works' -L -i
    dois = [] # list of DOIs to fetch
    papers = [] # list of papers created
    records_found = 0 # how many records did we successfully import from the profile?

    # Fetch publications
    pubs = jpath('orcid-profile/orcid-activities/orcid-works/orcid-work', profile, [])
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

        if doi and use_doi:
            continue

        # Extract information from ORCiD

        # Title
        title = j('work-title/title/value')
        if title is None:
            print "Warning: Skipping ORCID publication: no title"
        
        # Type
        doctype = orcid_to_doctype(j('work-type', 'other'))

        # Contributors (ignored for now as they are very often not present)
        def get_contrib(js):
            return {
                 'orcid':jpath('contributor-orcid', js),
                 'name': jpath('credit-name/value', js),
                }
        contributors = map(get_contrib, j('work-contributors/contributor',[]))

        author_names = filter(lambda x: x is not None, map(
                              lambda x: x['name'], contributors))
        authors = map(parse_comma_name, author_names)
        pubdate = None
        # ORCiD internal id
        identifier = j('put-code')
        affiliations = map(lambda x: x['orcid'], contributors)
        # Pubdate
        year = parse_int(j('publication-date/year/value'), 1970)
        month = parse_int(j('publication-date/month/value'), 01)
        day = parse_int(j('publication-date/day/value'), 01)
        pubdate = date(year=year, month=month, day=day)

        # Citation type: metadata format
        citation_format = j('work-citation/work-citation-type')
        print citation_format
        bibtex = j('work-citation/citation')

        if bibtex is not None:
            try:
                entry = parse_bibtex(bibtex)

                if entry.get('author', []) == []:
                    print "Warning: Skipping ORCID publication: no authors."
                    print j('work-citation/citation')
                if not authors:
                    authors = entry['author']
            except ValueError:
                pass

        affiliations = affiliate_author_with_orcid(ref_name, id, authors, initial_affiliations=affiliations)

        authors = map(name_lookup_cache.lookup, authors)

        if not authors:
            print "No authors found, skipping"
            continue

        # Create paper:
        paper = backend.create.get_or_create_paper(title, authors, pubdate, None, 'VISIBLE', affiliations)
        record = OaiRecord.new(
                source=orcid_oai_source,
                identifier=identifier,
                about=paper,
                splash_url='http://orcid.org/'+id,
                pubtype=doctype)
        records_found += 1

    if use_doi:
        doi_metadata = fetch_dois(dois)
        for metadata in doi_metadata:
            try:
                authors = map(convert_to_name_pair, metadata['author'])
                affiliations = affiliate_author_with_orcid(ref_name, id, authors)
                records_found += 1
                paper = save_doi_metadata(metadata, affiliations)
                record = OaiRecord.new(
                        source=orcid_oai_source,
                        identifier='orcid:'+id+':'+metadata['DOI'],
                        about=paper,
                        splash_url='http://orcid.org/'+id,
                        pubtype=paper.doctype)
            except (KeyError, ValueError, TypeError):
                pass

    return records_found

orcid_oai_source, _ = OaiSource.objects.get_or_create(identifier='orcid',
            defaults={'name':'ORCID','oa':False,'priority':1,'default_pubtype':'other'})

