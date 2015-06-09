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
from backend.crossref import fetch_publications
from backend.proxy import *
from backend.oai import *
from backend.core import fetch_papers_from_core_for_researcher
from backend.base import fetch_papers_from_base_for_researcher
from backend.name_cache import name_lookup_cache


logger = get_task_logger(__name__)

@shared_task(name='fetch_everything_for_researcher')
def fetch_everything_for_researcher(pk):
    try:
        r = Researcher.objects.get(pk=pk)
        fetch_dois_for_researcher(pk)
        fetch_records_for_researcher(pk)
        fetch_papers_from_core_for_researcher(r)
        #fetch_papers_from_base_for_researcher(Researcher.objects.get(pk=pk))
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

@shared_task(name='recluster_researcher')
def recluster_researcher(pk):
    r = Researcher.objects.get(pk=pk)
    clustering_context_factory.reclusterBatch(r

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
    fetch_publications(researcher)

@shared_task(name='change_publisher_oa_status')
def change_publisher_oa_status(pk, status):
    publisher = Publisher.objects.get(pk=pk)
    publisher.change_oa_status(status)
    publisher.update_stats()

