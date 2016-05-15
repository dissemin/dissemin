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
from notification.api import add_notification_for, delete_notification_per_tag
import notification.levels as notification_levels

from papers.errors import MetadataSourceException
from papers.doi import to_doi
from papers.name import match_names, normalize_name_words, parse_comma_name, shallower_name_similarity
from papers.utils import validate_orcid, parse_int, try_date
from papers.models import OaiSource
from papers.baremodels import BarePaper, BareOaiRecord
from papers.bibtex import parse_bibtex
from papers.orcid import *

from backend.papersource import PaperSource
from backend.crossref import fetch_dois, CrossRefPaperSource, convert_to_name_pair
from backend.name_cache import name_lookup_cache

from django.conf import settings

import requests, json

### Metadata manipulation utilities ####

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

orcid_oai_source, _ = OaiSource.objects.get_or_create(identifier='orcid',
            defaults={'name':'ORCID','oa':False,'priority':1,'default_pubtype':'other'})


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
    affiliations = [None]*len(authors)
    if initial_affiliations and len(initial_affiliations) == len(authors):
        affiliations = initial_affiliations
    if max_sim_idx is not None:
        affiliations[max_sim_idx] = orcid
    return affiliations

### Paper fetching ####

class SkippedPaper(Exception):
    pass

class ORCIDDataPaper(object):

    def __init__(self, ref_name, orcid_id, pub, stop_if_dois_exists=False):
        """
        stop_if_dois_exists: if we find any dois, we don't extract everything, just the dois.
        """

        self._pub = pub

        self.ref_name = ref_name
        self.id = orcid_id

        self.authors = []
        self.title = None
        self.pubdate = None

        self.skipped = False

        try:
            self._extract_dois()
            if self.dois and stop_if_dois_exists:
                return

            self._extract_title()
            self._extract_type()
            # self._extract_contributors()
            # self._extract_authors_from_contributors()
            self._extract_pubdate()
            self._extract_internal_identifier()

            self._extract_citation_format()
            self._extract_authors_from_bibtex()

            self._extract_affiliations()
            self._convert_authors()

            # These are the basic minimal information required for a BarePaper.
            if not self.authors or not self.title or not self.pubdate:
                raise SkippedPaper
        except SkippedPaper:
            self.skipped = True

    def _extract_dois(self):
        # DOIs
        self.dois = []
        for extid in self.j('work-external-identifiers/work-external-identifier', []):
            if extid.get('work-external-identifier-type') == 'DOI':
                doi = to_doi(jpath('work-external-identifier-id/value', extid))
                if doi:
                    # If a DOI is available, create the paper using metadata from CrossRef.
                    # We don't do it yet, we only store the DOI, so that we can fetch them
                    # by batch later.
                    self.dois.append(doi)


    def _extract_title(self):
        # Title
        self.title = self.j('work-title/title/value')
        if self.title is None:
            print "Warning: Skipping ORCID publication: no title"
            raise SkippedPaper

    def _extract_type(self):
        # Type
        self.doctype = orcid_to_doctype(self.j('work-type', 'other'))

    def _extract_contributors(self):
        # Contributors (ignored for now as they are very often not present)
        def get_contrib(js):
            return {
                    'orcid': jpath('contributor-orcid', js),
                    'name': jpath('credit-name/value', js),
            }

        self.contributors = map(get_contrib, self.j('work-contributors/contributor', []))

    def _extract_authors_from_contributors(self):
        author_names = filter(lambda x: x is not None,
                map(lambda x: x['name'], self.contributors)) # all contributors names which are not null
        self.authors = map(parse_comma_name, author_names)

    def _extract_pubdate(self):
        # Pubdate
        # Remark(RaitoBezarius): we don't want to put 01 ; it could be interpreted as octal 1.
        year = parse_int(self.j('publication-date/year/value'), 1970)
        month = parse_int(self.j('publication-date/month/value'), 1)
        day = parse_int(self.j('publication-date/day/value'), 1)
        self.pubdate = try_date(year, month, day) or try_date(year, month, 1) or try_date(year, 1, 1)
        if self.pubdate is None:
            print "Invalid publication date in ORCID publication, skipping"
            raise SkippedPaper

    def _extract_affiliations(self):
        """
        Dependent on authors.
        Once we have contributors, we should fetch initial affiliations based on the contributors.
        """
        self.affiliations = affiliate_author_with_orcid(self.ref_name, self.id, self.authors, initial_affiliations=[])

    def _extract_internal_identifier(self):
        # ORCiD internal id
        self.identifier = self.j('put-code')

    def _extract_citation_format(self):
        self.citation_format = self.j('work-citation/work-citation-type')
        print "ORCID publication (%s) uses %s citation format" % (self.title, self.citation_format)

    def _extract_authors_from_bibtex(self):
        self.bibtex = self.j('work-citation/citation')

        if self.bibtex is not None:
            try:
                entry = parse_bibtex(self.bibtex)

                if 'author' not in entry or len(entry['author']) == 0:
                    print "Warning: Skipping ORCID publication: no authors."
                    print self.bibtex
                    raise SkippedPaper
                else:
                    self.authors = entry['author']

            except ValueError:
                pass

    def _convert_authors(self):
        self.authors_converted = map(name_lookup_cache.lookup, self.authors)

    def __repr__(self):
        return '<ORCIDDataPaper %s written by %s>' % (self.title, ', '.join(self.authors))

    def __str__(self):
        return self.title

    def j(self, path, default=None):
        return jpath(path, self._pub, default)

    @property
    def splash_url(self):
        return 'http://{}/{}'.format(settings.ORCID_BASE_DOMAIN, self.id)



class OrcidPaperSource(PaperSource):
    def fetch_papers(self, researcher):
        self.researcher = researcher
        if researcher.orcid:
            if researcher.empty_orcid_profile == None:
                self.update_empty_orcid(researcher, True)
            return self.fetch_orcid_records(researcher.orcid)
        return []

    def create_paper(self, data_paper):
        assert (not data_paper.skipped)
        # Create paper
        paper = BarePaper.create(
            data_paper.title,
            data_paper.authors_converted,
            data_paper.pubdate,
            'VISIBLE',
            data_paper.affiliations
        )
        record = BareOaiRecord(
            source=orcid_oai_source,
            identifier=data_paper.identifier,
            splash_url=data_paper.splash_url,
            pubtype=data_paper.doctype
        )

        paper.add_oairecord(record)

        return paper

    def fetch_crossref_incrementally(self, crps, orcid_id):
        for metadata in crps.search_for_dois_incrementally('', {'orcid': orcid_id}):
            try:
                paper = crps.save_doi_metadata(metadata)
                if paper:
                    yield True, paper
                else:
                    yield False, metadata
            except ValueError as e:
                print "Saving CrossRef record from ORCID failed: %s" % unicode(e)

    def fetch_metadata_from_dois(self, crps, ref_name, orcid_id, dois):
        doi_metadata = fetch_dois(dois)
        for metadata in doi_metadata:
            try:
                authors = map(convert_to_name_pair, metadata['author'])
                affiliations = affiliate_author_with_orcid(ref_name, orcid_id, authors)
                paper = crps.save_doi_metadata(metadata, affiliations)
                if not paper:
                    yield False, metadata
                    continue

                record = BareOaiRecord(
                        source=orcid_oai_source,
                        identifier='orcid:%s:%s' % (orcid_id, metadata['DOI']),
                        splash_url='http://%s/%s' % (settings.ORCID_BASE_DOMAIN, orcid_id),
                        pubtype=paper.doctype)
                paper.add_oairecord(record)
                yield True, paper
            except (KeyError, ValueError, TypeError):
                yield False, metadata

    def warn_user_of_ignored_papers(self, ignored_papers):
        user = self.researcher.user
        if user is not None:
            delete_notification_per_tag(user, 'backend_orcid')
            notification = {
                'code': 'IGNORED_PAPERS',
                'papers': ignored_papers
            }
            add_notification_for([user],
                    notification_levels.ERROR,
                    notification,
                    'backend_orcid'
            )

    def fetch_orcid_records(self, orcid_identifier, profile=None, use_doi=True):
        """
        Queries ORCiD to retrieve the publications associated with a given ORCiD.
        It also fetches such papers from the CrossRef search interface.

        :param profile: The ORCID profile if it has already been fetched before (format: parsed JSON).
        :param use_doi: Fetch the publications by DOI when we find one (recommended, but slow)
        :returns: a generator, where all the papers found are yielded. (some of them could be in
                free form, hence not imported)
        """
        crps = CrossRefPaperSource(self.ccf)

        # Cleanup iD:
        orcid_id = validate_orcid(orcid_identifier)
        if orcid_id is None:
            raise MetadataSourceException('Invalid ORCiD identifier')

        # Get ORCiD profile
        try:
            if profile is None:
                profile = OrcidProfile(id=orcid_id)
            else:
                profile = OrcidProfile(json=profile)
        except MetadataSourceException as e:
            print e
            return

        # Reference name
        ref_name = profile.name
        # curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0002-8612-8827/orcid-works' -L -i
        dois = [] # list of DOIs to fetch
        ignored_papers = [] # list of ignored papers due to incomplete metadata

        # Fetch publications (1st attempt with ORCiD data)
        pubs = jpath('orcid-profile/orcid-activities/orcid-works/orcid-work', profile, [])
        for pub in pubs:
            data_paper = ORCIDDataPaper(ref_name, orcid_id, pub, stop_if_dois_exists=use_doi)

            if data_paper.dois and use_doi: # We want to batch it rather than manually do it.
                dois.extend(data_paper.dois)
                continue

            # Extract information from ORCiD
            if data_paper.skipped:
                print ('%s is skipped due to incorrect metadata' % (data_paper))
                ignored_papers.append(pub)
                continue

            yield self.create_paper(data_paper)
        
        # 2nd attempt with DOIs and CrossRef
        if use_doi:
            # Let's grab papers from CrossRef
            for success, paper_or_metadata in self.fetch_crossref_incrementally(crps, orcid_id):
                if success:
                    yield paper_or_metadata
                else:
                    ignored_papers.append(paper_or_metadata)
                    print ('This metadata (%s) yields no paper.' % (metadata))

            # Let's grab papers with DOIs found in our ORCiD profile.
            # FIXME(RaitoBezarius): if we fail here, we should get back the pub and yield it.
            for success, paper_or_metadata in self.fetch_metadata_from_dois(crps, ref_name, orcid_id, dois):
                if success:
                    yield paper_or_metadata
                else:
                    ignored_papers.append(paper_or_metadata)
                    print ('This metadata (%s) yields no paper.' % (paper_or_metadata))
       
        if ignored_papers:
            self.warn_user_of_ignored_papers(ignored_papers)
            print ('Warning: Total ignored papers: %d' % (len(ignored_papers)))
