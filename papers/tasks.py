# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re

from celery import shared_task
from celery.utils.log import get_task_logger
from celery import current_task

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError

from papers.models import *
from papers.backend import *
from papers.oai import *
from papers.doi import to_doi
from papers.crossref import fetch_papers_from_crossref_by_researcher_name, convert_to_name_pair

logger = get_task_logger(__name__)

def process_records(listRecords, source):
    count = 0
    saved = 0
    for record in listRecords:
        # Update task status
        if count % 100 == 0:
        source.status = '%d records processed, %d records saved' % (count,saved)
        source.save()
        count += 1

        metadata = record[1]._map
        authors = get_oai_authors(metadata)

        # Filter the record
        if all(not elem.is_known for elem in authors):
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

        logger.info('Saving record %s' % record[0].identifier())
        paper = get_or_create_paper(metadata['title'][0], authors, year, doi) # TODO replace with real pubdate
        # Save the record
        add_oai_record(record, source, paper)
        saved += 1
   return (count,saved)


@shared_task
def fetch_items_from_oai_source(pk):
    source = OaiSource.objects.get(pk=pk) # this is safe because the PK is checked by the view
    try:
        # Set up the OAI fetcher
        registry = MetadataRegistry()
        registry.registerReader('oai_dc', oai_dc_reader)
        client = Client(source.url, registry)
        client.updateGranularity()

        start_date = source.last_update.replace(tzinfo=None)
        restrict_set = source.restrict_set
        try:
            if restrict_set:
                listRecords = client.listRecords(metadataPrefix='oai_dc', from_= start_date, set=restrict_set)
            else:
                listRecords = client.listRecords(metadataPrefix='oai_dc', from_= start_date)
            # TODO make it less naive, for instance convert to UTC beforehand
        except NoRecordsMatchError:
            listRecords = []
        
        (count,saved) = process_records(listRecords, source)

        # Save the current date
        source.status = 'OK, %d records fetched.' % count
        source.last_update = timezone.now()
        source.save()
    except Exception as e:
        source.status = 'ERROR: '+unicode(e)
        source.save()
        raise

@shared_task
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    try:
        researcher.status = 'Fetching DOI list.'
        researcher.save()
        nb_records = 0

        for name in researcher.name_set.all():
            lst = fetch_papers_from_crossref_by_researcher_name(name)

            researcher.status = 'Saving %d records' % len(lst)
            researcher.save()

            for metadata in lst:
                if not 'title' in metadata or not metadata['title']:
                    print "No title, skipping"
                    continue # TODO at many continue, add warnings in logs
                if not 'DOI' in metadata or not metadata['DOI']:
                    print "No DOI, skipping"
                    continue
                doi = to_doi(metadata['DOI'])

                try:
                    d = Publication.objects.get(doi=doi)
                    paper = d.paper
                except ObjectDoesNotExist:
                    year = None
                    try:
                        year = int(metadata['issued']['date-parts'][0][0])
                    except Exception:
                        pass
                    if not year:
                        try:
                            year = int(metadata['deposited']['date-parts'][0][0])
                        except Exception:
                            pass

                    if not year:
                        print "No year, skipping"
                        continue
                    
                    title = metadata['title']
                    authors = map(lookup_name, map(convert_to_name_pair, metadata['author']))
                    paper = get_or_create_paper(title, authors, year) # don't let this function
                    # create the publication, because it would re-fetch the metadata from CrossRef
                    create_publication(paper, metadata)
            nb_records += len(lst)

        researcher.status = 'OK, %d records processed.' % nb_records
        researcher.save()
        # TODO remove me"
    except ValueError as e:
        researcher.status = 'ERROR: %s' % unicode(e)
        researcher.save()
        raise e


