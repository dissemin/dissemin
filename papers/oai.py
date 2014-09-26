# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError

from papers.backend import *
from papers.models import OaiRecord, OaiSource

import re

def add_oai_record(record, source, paper=None):
    """ Add a record (from OAI-PMH) to the local database """
    header = record[0]
    identifier = header.identifier()

    matching = OaiRecord.objects.filter(identifier=identifier)
    if len(matching) > 0:
        return # Record already saved. TODO : update if information changed

    # Build the URL
    url = ''
    if 'identifier' in record[1]._map:
        for iden in record[1]._map['identifier']:
            iden = iden.strip()
            if iden.startswith(source.prefix_identifier):
                url = source.prefix_url+iden[len(source.prefix_identifier):]

    r = OaiRecord(source=source,identifier=identifier,about=paper,url=url)
    r.save()

comma_re = re.compile(r',+')

def parse_oai_author(name):
    """ Parse an name of the form "Last name, First name" to (first name, last name) """
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
    """ Get the authors out of a search result """
    return map(lookup_author, map(parse_oai_author, metadata['creator']))

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

