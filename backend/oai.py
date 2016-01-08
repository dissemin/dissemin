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

import itertools
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError, BadArgumentError

from papers.name import parse_comma_name, name_normalization, name_signature, normalize_name_words
from papers.models import OaiRecord, OaiSource, Name
from papers.baremodels import BareOaiRecord, BarePaper
from papers.doi import to_doi
from papers.utils import sanitize_html

from backend.papersource import *
from backend.extractors import *
from backend.proxy import *
from backend.name_cache import name_lookup_cache
from backend.pubtype_translations import *
from backend import crossref

import re

def get_oai_authors(metadata):
    """ Get the authors names out of a search result """
    return map(name_lookup_cache.lookup, map(parse_comma_name, metadata['creator']))

def find_earliest_oai_date(record):
    """ Find the latest publication date (if any) in a record """
    earliest = None
    for date in record[1]._map['date']:
        try:
            parsed = tolerant_datestamp_to_datetime(date)
            if earliest is None or parsed < earliest:
                earliest = parsed
        except (DatestampError, ValueError):
            continue
    return earliest

def add_oai_record(record, source, paper):
    """ Add a record (from OAI-PMH) to the given paper """
    header = record[0]
    identifier = header.identifier()

    # A description is useful
    curdesc = ""
    for desc in record[1]._map['description']:
        if len(desc) > len(curdesc):
                curdesc = desc
    curdesc = sanitize_html(curdesc)

    # Run extractor to find the URLs
    pdf_url = None
    splash_url = None
    if source.identifier:
        try:
            extractor = REGISTERED_EXTRACTORS[source.identifier]
            urls = extractor.extract(record)
            pdf_url = urls.get('pdf')
            splash_url = urls.get('splash')
        except KeyError:
            print "Warning, invalid extractor for source "+source.name

    keywords = ' '.join(record[1]._map['subject'])
    contributors = ' '.join(record[1]._map['contributor'])[:4096]

    pubtype_list = record[1]._map.get('type')
    pubtype = None
    if len(pubtype_list) > 0:
        pubtype = pubtype_list[0]
    #pubtype = source.default_pubtype
    pubtype = PUBTYPE_TRANSLATIONS.get(pubtype, source.default_pubtype)

    record = BareOaiRecord(
            source=source,
            identifier=identifier,
            description=curdesc,
            keywords=keywords,
            contributors=contributors,
            pubtype=pubtype,
            pdf_url=pdf_url,
            splash_url=splash_url)
    paper.add_oairecord(record)

def listRecords_or_empty(source, *args, **kwargs):
    """
    pyoai raises :class:`NoRecordsMatchError` when no records match,
    we would rather like to get an empty list in that case.
    """
    try:
        return source.listRecords(*args, **kwargs)
    except NoRecordsMatchError:
        return []

class OaiPaperSource(PaperSource):
    """
    A paper source that fetches records from the OAI-PMH proxy.
    """
    def __init__(self, *args, **kwargs):
        super(OaiPaperSource, self).__init__(*args, **kwargs)
        self.client = get_proxy_client()
        self.base = get_base_client()

    def fetch_papers(self, researcher):
        return self.fetch_records_for_name(researcher.name, signature=False)

    #### Record search utilities

    def fetch_records_for_name(self, name, signature=True):
        """
        Fetch all papers that match a given signature (first initial and full last name),
        or that match the full name if signature is set to False.
        """
        if signature:
            return self.fetch_records_for_signature(name_signature(name.first, name.last))
        else:
            return self.fetch_records_for_full_name(name.first, name.last)

    def fetch_records_for_fingerprint(self, ident):
        """
        Fetch all the records that match a given paper fingerprint.
        """
        print "fetch_records_for_fingerprint: THIS IS DEPRECATED"
        listRecords = listRecords_or_empty(self.client,
                metadataPrefix='base_dc', set=PROXY_FINGERPRINT_PREFIX+ident)
        return self.process_records(listRecords)

    def fetch_accessibility(self, paper):
        """
        Computes the accessibility of a given paper,
        by fetching preprints from OAI-PMH
        """
        records = listRecords_or_empty(self.base,
                metadataPrefix='base_dc',
                set=PROXY_FINGERPRINT_PREFIX+paper.fingerprint)

        for publi in paper.publications:
            records = itertools.chain(records, listRecords_or_empty(self.base,
                metadataPrefix='base_dc',
                set=PROXY_DOI_PREFIX+publi.doi))

        for record in records:
            # Find the source
            sets = record[0].setSpec()
            source_identifier = None
            for s in sets:
                if s.startswith(PROXY_SOURCE_PREFIX):
                    source_identifier = s[len(PROXY_SOURCE_PREFIX):]
                    break
            source = None
            if source_identifier:
                try:
                    source = OaiSource.objects.get(identifier=source_identifier)
                except OaiSource.DoesNotExist:
                    pass
            if not source:
                print "Invalid source '"+str(source_identifier)+"' from the proxy, skipping"
                continue

            # Save the record
            try:
                add_oai_record(record, source, paper)
            except ValueError as e:
                print "Warning, OAI record "+record[0].identifier()+" skipped:\n"+unicode(e)

        paper.update_availability()
        return paper

    def fetch_records_for_signature(self, ident):
        try:
            listRecords = listRecords_or_empty(self.client,
                    metadataPrefix='oai_dc', set=PROXY_SIGNATURE_PREFIX+ident)
            return self.process_records(listRecords)
        except BadArgumentError as e:
            print "Signature is unknown for the proxy: "+unicode(e)
            pass
        return []

    def fetch_records_for_full_name(self, firstname, lastname):
        try:
            ident = name_normalization(lastname+', '+firstname)
            listRecords = self.client.listRecords(metadataPrefix='oai_dc', set=PROXY_AUTHOR_PREFIX+ident)
            for p in self.process_records(listRecords):
                yield p
            ident = name_normalization(firstname+' '+lastname)
            listRecords = listRecords_or_empty(self.client,
                    metadataPrefix='oai_dc', set=PROXY_AUTHOR_PREFIX+ident)
            for p in self.process_records(listRecords):
                yield p
        except BadArgumentError as e:
            print "Author is unknown for the proxy: "+unicode(e)
            pass
    
    def process_records(self, listRecords):
        for record in listRecords:
            metadata = record[1]._map
            authors = get_oai_authors(metadata)

            # Filter the record
            if all(not elem.is_known for elem in authors):
                print "No relevant author, continue"
                continue
            if not 'title' in metadata or metadata['title'] == []:
                continue

            # Find the source
            sets = record[0].setSpec()
            source_identifier = None
            for s in sets:
                if s.startswith(PROXY_SOURCE_PREFIX):
                    source_identifier = s[len(PROXY_SOURCE_PREFIX):]
                    break
            source = None
            if source_identifier:
                try:
                    source = OaiSource.objects.get(identifier=source_identifier)
                except OaiSource.DoesNotExist:
                    pass
            if not source:
                print "Invalid source '"+str(source_identifier)+"' from the proxy, skipping"
                continue

            # Find the DOI, if any
            doi = None
            for identifier in metadata['identifier']+metadata['relation']:
                if not doi:
                    doi = to_doi(identifier)

            # A publication date is necessary
            pubdate = find_earliest_oai_date(record)
            if not pubdate:
                print "No publication date, skipping"
                continue

            print 'Saving record %s' % record[0].identifier()
            paper = BarePaper.create(metadata['title'][0], authors, pubdate)

            if doi:
                try:
                    metadata = crossref.fetch_metadata_by_DOI(doi)
                    crossref.create_publication(paper, metadata)
                except MetadataSourceException as e:
                    print("Warning, metadata source exception while fetching DOI "+doi+":\n"+unicode(e))
                    pass


            if paper is None:
                print "Paper creation failed, skipping"
                continue

            # Save the record
            # TODO: we should check record validity *BEFORE* creating the paper
            try:
                add_oai_record(record, source, paper)
                yield paper
            except ValueError as e:
                print "Warning, OAI record "+record[0].identifier()+" skipped:\n"+unicode(e)
                paper.update_availability()


