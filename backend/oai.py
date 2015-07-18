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

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError

from papers.name import parse_comma_name, normalize_name_words
from papers.models import OaiRecord, OaiSource, Name
from papers.doi import to_doi

from backend.oai import *

# Reader slightly tweaked because Cairn includes a useful non-standard field
my_oai_dc_reader = oai_dc_reader
my_oai_dc_reader._fields['accessRights'] = ('textList', 'oai_dc:dc/dcterms:accessRights/text()')
my_oai_dc_reader._namespaces['dcterms'] = 'http://purl.org/dc/terms/'

from backend.extractors import *
from backend.proxy import PROXY_SOURCE_PREFIX
from backend.create import *
from backend.name_cache import name_lookup_cache
from backend.pubtype_translations import *

import re


def process_records(listRecords):
    count = 0
    saved = 0
    for record in listRecords:
        count += 1

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
            except ObjectDoesNotExist:
                pass
        if not source:
            print "Invalid source '"+str(source_identifier)+"' from the proxy, skipping"
            continue

        # Find the DOI, if any
        doi = None
        for identifier in metadata['identifier']:
            if not doi:
                doi = to_doi(identifier)

        # A publication date is necessary
        pubdate = find_earliest_oai_date(record)
        if not pubdate:
            print "No publication date, skipping"
            continue

        print 'Saving record %s' % record[0].identifier()
        paper = get_or_create_paper(metadata['title'][0], authors, pubdate, doi)
        if paper is None:
            print "Paper creation failed, skipping"
            continue

        # Save the record
        try:
            add_oai_record(record, source, paper)
            saved += 1
        except ValueError as e:
            print "Warning, OAI record "+identifier+" skipped:\n"+unicode(e)
            if paper.is_orphan():
                paper.visibility = 'CANDIDATE'
                paper.save(update_fields=['visibility'])
    return (count,saved)


def add_oai_record(record, source, paper=None):
    """ Add a record (from OAI-PMH) to the local database """
    header = record[0]
    identifier = header.identifier()

    # A description is useful
    curdesc = ""
    for desc in record[1]._map['description']:
        if len(desc) > len(curdesc):
                curdesc = desc

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

    pubtype = record[1]._map.get('type')
    pubtype = source.default_pubtype
    #pubtype = PUBTYPE_TRANSLATIONS.get(pubtype, source.default_pubtype)

    OaiRecord.new(
            source=source,
            identifier=identifier,
            about=paper,
            description=curdesc,
            keywords=keywords,
            contributors=contributors,
            pubtype=pubtype,
            pdf_url=pdf_url,
            splash_url=splash_url)


def get_oai_authors(metadata):
    """ Get the authors names out of a search result """
    return map(name_lookup_cache.lookup, map(parse_comma_name, metadata['creator']))

def find_earliest_oai_date(record):
    """ Find the latest publication date (if any) in a record """
    earliest = None
    for date in record[1]._map['date']:
        try:
            parsed = tolerant_datestamp_to_datetime(date)
            if earliest == None or parsed < earliest:
                earliest = parsed
        except DatestampError:
            continue
        except ValueError:
            continue
    return earliest

