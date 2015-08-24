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

from backend.create import *
from backend.crossref import fetch_publications
from backend.oai import *
from backend.core import fetch_papers_from_core_for_researcher
from backend.base import fetch_papers_from_base_for_researcher
from backend.orcid import fetch_orcid_records
from backend.name_cache import name_lookup_cache
from backend.extractors import * # to ensure that OaiSources are created
from backend.utils import run_only_once

logger = get_task_logger(__name__)

def update_researcher_task(r, task_name):
    """
    Update the task identifier associated to a given researcher.
    This also updates the 'last_harvest' field.
    """
    r.current_task = task_name
    r.last_harvest = timezone.now()
    r.save(update_fields=['current_task','last_harvest'])


@shared_task(name='init_profile_from_orcid')
@run_only_once('researcher', keys=['pk'])
def init_profile_from_orcid(pk):
    """
    Populates the profile from ORCID and Proaixy.
    Does not fetch DOIs from ORCID as it can be slow.

    This task is intended to be very quick, so that users
    can see their ORCID publications quickly.
    """
    try:
        r = Researcher.objects.get(pk=pk)
        update_task = lambda name: update_researcher_task(r, name)
        update_task('clustering')
        clustering_context_factory.reclusterBatch(r)
        if r.orcid:
            update_task('orcid')
            num = fetch_orcid_records(r.orcid, use_doi=False)
            r.empty_orcid_profile = (num == 0)
            r.save(update_fields=['empty_orcid_profile'])
        if r.empty_orcid_profile != False:
            update_task('crossref')
            fetch_dois_for_researcher(pk)
        update_task('oai')
        fetch_records_for_researcher(pk)
    finally:
        update_task('clustering')
        clustering_context_factory.commitThemAll()
        clustering_context_factory.unloadResearcher(pk)
        r = Researcher.objects.get(pk=pk)
        update_task('stats')
        r.update_stats()
        update_task(None)



@shared_task(name='fetch_everything_for_researcher')
@run_only_once('researcher', keys=['pk'], timeout=15*60)
def fetch_everything_for_researcher(pk):
    try:
        r = Researcher.objects.get(pk=pk)
        update_task = lambda name: update_researcher_task(r, name)
        if r.orcid:
            update_task('orcid')
            num = fetch_orcid_records(r.orcid)
            r.empty_orcid_profile = (num == 0)
            r.save(update_fields=['empty_orcid_profile'])
        update_task('crossref')
        fetch_dois_for_researcher(pk)
        update_task('oai')
        fetch_records_for_researcher(pk)
        update_task('core')
        fetch_papers_from_core_for_researcher(r)
        #fetch_papers_from_base_for_researcher(Researcher.objects.get(pk=pk))
    except MetadataSourceException as e:
        raise e
    finally:
        update_task('clustering')
        clustering_context_factory.commitThemAll()
        clustering_context_factory.unloadResearcher(pk)
        r = Researcher.objects.get(pk=pk)
        update_task('stats')
        r.update_stats()
        r.harvester = None
        update_task(None)

@shared_task(name='fetch_records_for_researcher')
def fetch_records_for_researcher(pk, signature=True):
    """
    Fetch OAI records from Proaixy for the given researcher.

    :param signature: Search by name signature (D. Knuth) instead
       of full name (Donald Knuth)
    """
    researcher = Researcher.objects.get(pk=pk)
    fetch_records_for_name(researcher.name, signature=signature)

@shared_task(name='recluster_researcher')
def recluster_researcher(pk):
    r = Researcher.objects.get(pk=pk)
    clustering_context_factory.reclusterBatch(r)
    r.update_stats()

@shared_task(name='fetch_dois_for_researcher')
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    fetch_publications(researcher)

@shared_task(name='change_publisher_oa_status')
def change_publisher_oa_status(pk, status):
    publisher = Publisher.objects.get(pk=pk)
    publisher.change_oa_status(status)
    publisher.update_stats()

