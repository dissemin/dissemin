# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError

from papers.backend import *
from papers.models import OaiRecord, OaiSource
from papers.utils import normalize_name_words
from papers.extractors import *

import re

# Reader slightly tweaked because Cairn includes a useful non-standard field
my_oai_dc_reader = oai_dc_reader
my_oai_dc_reader._fields['accessRights'] = ('textList', 'oai_dc:dc/dcterms:accessRights/text()')
my_oai_dc_reader._namespaces['dcterms'] = 'http://purl.org/dc/terms/'


def add_oai_record(record, source, paper=None):
    """ Add a record (from OAI-PMH) to the local database """
    header = record[0]
    identifier = header.identifier()

    matching = OaiRecord.objects.filter(identifier=identifier)
    if len(matching) > 0:
        print "Record already saved"
        return # Record already saved. TODO : update if information changed

    # A description is useful
    curdesc = ""
    for desc in record[1]._map['description']:
        if len(desc) > len(curdesc):
                curdesc = desc

    # Run extractor to find the URLs
    pdf_url = None
    splash_url = None
    if source.url_extractor:
        try:
            extractor = REGISTERED_EXTRACTORS[source.url_extractor]
            urls = extractor.extract(record)
            pdf_url = urls.get('pdf')
            splash_url = urls.get('splash')
        except KeyError:
            print "Warning, invalid extractor for source "+source.name

    r = OaiRecord(
            source=source,
            identifier=identifier,
            about=paper,
            description=curdesc,
            pdf_url=pdf_url,
            splash_url=splash_url)
    r.save()

comma_re = re.compile(r',+')

def parse_oai_author(name):
    """ Parse an name of the form "Last name, First name" to (first name, last name) """
    name = normalize_name_words(name)
    name = comma_re.sub(',',name)
    first_name = ''
    last_name = name
    idx = name.find(',')
    if idx != -1:
        last_name = name[:idx]
        first_name = name[(idx+1):]
    first_name = first_name.strip()
    last_name = last_name.strip()
    return (first_name,last_name)

def get_oai_authors(metadata):
    """ Get the authors names out of a search result """
    return map(lookup_name, map(parse_oai_author, metadata['creator']))

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

