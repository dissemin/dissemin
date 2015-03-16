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
from papers.doi import to_doi
from papers.name import name_normalization, name_signature

from backend.create import *
from backend.crossref import fetch_papers_from_crossref_by_researcher_name, convert_to_name_pair
from backend.proxy import *
from backend.oai import *
from backend.base import fetch_papers_from_base_for_researcher
from backend.name_cache import name_lookup_cache


logger = get_task_logger(__name__)

@shared_task(name='fetch_everything_for_researcher')
def fetch_everything_for_researcher(pk):
    try:
        fetch_records_for_researcher(pk)
        fetch_dois_for_researcher(pk)
        fetch_papers_from_base_for_researcher(Researcher.objects.get(pk=pk))
    except MetadataSourceException as e:
        raise e
    finally:
        clustering_context_factory.commitThemAll()
        clustering_context_factory.unloadResearcher(pk)
        r = Researcher.objects.get(pk=pk)
        r.update_stats()

@shared_task(name='fetch_records_for_researcher')
def fetch_records_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    fetch_records_for_name(researcher.name)

def fetch_records_for_name(name):
    fetch_records_for_signature(name_signature(name.first, name.last))

def fetch_records_for_signature(ident):
    client = get_proxy_client()
    try:
        listRecords = client.listRecords(metadataPrefix='oai_dc', set=PROXY_SIGNATURE_PREFIX+ident)
        process_records(listRecords)
    except NoRecordsMatchError:
        pass
    except BadArgumentError as e:
        print "Signature is unknown for the proxy: "+unicode(e)
        pass

# TODO unused:
def fetch_records_for_last_name(lastname):
    client = get_proxy_client()
    try:
        ident = name_normalization(lastname)
        listRecords = client.listRecords(metadataPrefix='oai_dc', set=PROXY_AUTHOR_PREFIX+ident)
        process_records(listRecords)
    except NoRecordsMatchError:
        pass
    except BadArgumentError as e:
        print "Author is unknown for the proxy: "+unicode(e)
        pass


@shared_task(name='fetch_dois_for_researcher')
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)

    researcher.status = 'Fetching DOI list.'
    researcher.save()
    nb_records = 0

    name = researcher.name
    lst = fetch_papers_from_crossref_by_researcher_name(name)

    researcher.status = 'Saving records'
    researcher.save()

    count = 0
    for metadata in lst:
        # the upstream function ensures that there is a non-empty title
        if not 'DOI' in metadata or not metadata['DOI']:
            print "No DOI, skipping"
            continue
        doi = to_doi(metadata['DOI'])

        try:
            d = Publication.objects.get(doi=doi)
            paper = d.paper
        except ObjectDoesNotExist:
            # TODO also parse plain dates, as in the following DOI:
            # http://dx.doi.org/10.13140/2.1.4250.8161
            # By the way, the following code is ugly
            pubdate = None
            try:
                pubdate = date_from_dateparts(metadata['issued']['date-parts'][0])
            except Exception:
                pass
            if not pubdate:
                try:
                    pubdate = date_from_dateparts(['deposited']['date-parts'][0])
                except Exception:
                    pass

            if not pubdate:
                print "No pubdate, skipping"
                continue
            
            title = metadata['title']
            authors = map(name_lookup_cache.lookup, map(convert_to_name_pair, metadata['author']))
            authors = filter(lambda x: x != None, authors)
            if all(not elem.is_known for elem in authors) or authors == []:
                continue
            print "# Saved."
            paper = get_or_create_paper(title, authors, pubdate) # don't let this function
            # create the publication, because it would re-fetch the metadata from CrossRef
            create_publication(paper, metadata)

            count += 1
    nb_records += count

    researcher.status = 'OK, %d records processed.' % nb_records
    researcher.save()


@shared_task(name='change_publisher_oa_status')
def change_publisher_oa_status(pk, status):
    publisher = Publisher.objects.get(pk=pk)
    publisher.change_oa_status(status)
    publisher.update_stats()

