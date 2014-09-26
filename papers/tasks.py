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
from papers.backend import *
from papers.oai import *
from papers.doi import to_doi
from papers.crossref import fetch_papers_from_crossref_by_researcher, convert_to_name_pair

logger = get_task_logger(__name__)


@shared_task
def fetch_items_from_oai_source(pk):
    source = OaiSource.objects.get(pk=pk) # TODO catch exception here
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
        authors = get_oai_authors(metadata)

        # Filter the record
        if all(type(elem) == type(()) for elem in authors):
            continue
        if not 'title' in metadata or metadata['title'] == []:
            continue

        # Find the DOI, if any
        doi = None
        for identifier in metadata['identifier']:
            if not doi:
                doi = to_doi(identifier)

        pubdate = find_earliest_oai_date(record)
        year = None
        if pubdate:
            year = pubdate.year
        else:
            print "No publication date, skipping"
            continue

        logger.info('Saving record '+record[0].identifier())
        paper = get_or_create_paper(metadata['title'][0], authors, year, doi) # TODO replace with real pubdate

        # Save the record
        add_oai_record(record, source, paper)
   
    # Save the current date
    source.last_update = timezone.now()
    source.save()

@shared_task
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    lst = fetch_papers_from_crossref_by_researcher(researcher)

    for metadata in lst:
        if not 'title' in metadata or not metadata['title']:
            print "No title, skipping"
            continue # TODO at many continue, add warnings in logs
        if not 'DOI' in metadata or not metadata['DOI']:
            print "No DOI, skipping"
            continue

        
        title = metadata['title']
        authors = map(lookup_author, map(convert_to_name_pair, metadata['author']))
        doi = to_doi(metadata['DOI'])
        get_or_create_paper(title, authors, timezone.now(), doi) # TODO replace with real pubdate


