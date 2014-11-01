# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import re

from celery import shared_task
from celery.utils.log import get_task_logger
from celery import current_task

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from oaipmh.datestamp import tolerant_datestamp_to_datetime
from oaipmh.error import DatestampError, NoRecordsMatchError, BadArgumentError

from papers.models import *
from papers.backend import *
from papers.oai import *
from papers.doi import to_doi
from papers.crossref import fetch_papers_from_crossref_by_researcher_name, convert_to_name_pair
from papers.proxy import *
from papers.utils import name_normalization

logger = get_task_logger(__name__)

def process_records(listRecords):
    count = 0
    saved = 0
    for record in listRecords:
        count += 1

        metadata = record[1]._map
        authors = get_oai_authors(metadata)

        # Filter the record
        if all(not elem.is_known for elem in authors):
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

        pubdate = find_earliest_oai_date(record)
        year = None
        if pubdate:
            year = pubdate.year
        else:
            print "No publication date, skipping"
            continue

        logger.info('Saving record %s' % record[0].identifier())
        paper = get_or_create_paper(metadata['title'][0], authors, year, doi)

        # Save the record
        add_oai_record(record, source, paper)
        saved += 1
    return (count,saved)

@shared_task
def fetch_records_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    for name in researcher.name_set.all():
        fetch_records_for_name(name)

def fetch_records_for_name(name):
    ident = name.last + ', ' + name.first
    ident = name_normalization(ident)
    client = get_proxy_client()
    try:
        listRecords = client.listRecords(metadataPrefix='oai_dc', set=PROXY_AUTHOR_PREFIX+ident)
        process_records(listRecords)
    except NoRecordsMatchError:
        pass
    except BadArgumentError:
        print "Author is unknown for the proxy"
        pass


@shared_task
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)

    researcher.status = 'Fetching DOI list.'
    researcher.save()
    nb_records = 0

    for name in researcher.name_set.all():
        lst = fetch_papers_from_crossref_by_researcher_name(name)

        researcher.status = 'Saving records'
        researcher.save()

        count = 0
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

                count += 1
        nb_records += count

    researcher.status = 'OK, %d records processed.' % nb_records
    researcher.save()

