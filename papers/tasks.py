# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re

from celery import shared_task
from celery.utils.log import get_task_logger

from django.utils import timezone

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError

from papers.models import *

logger = get_task_logger(__name__)

def add_record(record, source, paper=None):
    """ Add a record (from OAI-PMH) to the local database """
    header = record[0]
    identifier = header.identifier()

    matching = OaiRecord.objects.filter(identifier=identifier)
    if len(matching) > 0:
        return # Record already saved. TODO : update if information changed
    r = OaiRecord(source=source,identifier=identifier,about=paper)
    r.save()

    # For each field
    for key in record[1]._map:
        values = record[1]._map[key]
        for v in values: 
            kv = OaiStatement(record=r,prop=key,value=v)
            kv.save()

comma_re = re.compile(r',+')

def parse_author(name):
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

def lookup_author(author):
    first_name = author[0]
    last_name = author[1]
    results = Researcher.objects.filter(first_name__iexact=first_name,last_name__iexact=last_name)
    if len(results) > 0:
        return results[0]
    else:
        return author

def get_authors(metadata):
    """ Get the authors out of a search result """
    return map(lookup_author, map(parse_author, metadata['creator']))

def get_or_create_paper(metadata, authors):
    # TODO improve this a lot
    title = metadata['title'][0]
    matches = Paper.objects.filter(title__iexact=title)
    if matches:
        return matches[0]
    p = Paper(title=title)
    p.save()
    for author in authors:
        if type(author) == type(()):
            a = Author(first_name=author[0],last_name=author[1],paper=paper)
        else:
            a = Author(first_name=author.first_name,
                       last_name=author.last_name,
                       paper=paper,
                       researcher=author)
        a.save()
    return p

@shared_task
def fetch_items_from_source(pk):
    source = OaiSource.objects.get(pk=pk)
    # Set up the OAI fetcher
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', oai_dc_reader)
    client = Client(source.url, registry)
    client.updateGranularity()

    # TODO handle errors and report them to the model.
    start_date = source.last_update.replace(tzinfo=None)
    try:
        listRecords = client.listRecords(metadataPrefix='oai_dc', from_= start_date, set="ENS-PARIS")
        # TODO make it less naive, for instance convert to UTC beforehand
    except NoRecordsMatchError:
        listRecords = []

    for record in listRecords:
        metadata = record[1]._map
        pubdate = find_latest_date(record)
        authors = get_authors(metadata)

        # Filter the record
        if all(type(elem) == type(()) for elem in authors):
            continue
        if not 'title' in metadata or metadata['title'] == []:
            continue

        logger.info('Saving record '+record[0].identifier())
        paper = get_or_create_paper(metadata, authors)

        # Save the record
        add_record(record, source, paper)
   
    # Save the current date
    source.last_update = timezone.now()
    source.save()


def find_latest_date(record):
    """ Find the latest publication date (if any) in a record """
    latest = None
    for date in record[1]._map['date']:
        try:
            parsed = tolerant_datestamp_to_datetime(date)
            if latest == None or parsed > latest:
                latest = parsed
        except DatestampError:
            continue
        except ValueError:
            continue
    return latest

