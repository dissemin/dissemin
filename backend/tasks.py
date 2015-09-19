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

from backend.globals import get_ccf
from backend.crossref import *
from backend.oai import *
from backend.core import CorePaperSource
from backend.base import BasePaperSource
from backend.orcid import *
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
    
    ccf = get_ccf()
    r = Researcher.objects.get(pk=pk)
    update_task = lambda name: update_researcher_task(r, name)
    update_task('clustering')
    ccf.reclusterBatch(r)
    fetch_everything_for_researcher(pk)

@shared_task(name='fetch_everything_for_researcher')
@run_only_once('researcher', keys=['pk'], timeout=15*60)
def fetch_everything_for_researcher(pk):
    ccf = get_ccf()
    oai = OaiPaperSource(ccf, max_results=250)
    sources = [
        ('orcid',OrcidPaperSource(ccf, oai, max_results=1000)),
        ('crossref',CrossRefPaperSource(ccf, oai, max_results=500)),
        ('oai',oai),
        ('base',BasePaperSource(ccf, max_results=200)),
       # ('core',CorePaperSource(ccf, max_results=250)),
       ]
    try:
        r = Researcher.objects.get(pk=pk)
        update_task = lambda name: update_researcher_task(r, name)
        for key,source in sources:
            update_task(key)
            source.fetch(r, incremental=True)
        update_task(None)

    except MetadataSourceException as e:
        raise e
    finally:
        update_task('clustering')
        ccf.commitThemAll()
        ccf.unloadResearcher(pk)
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
    ccf = get_ccf()
    try:
        r = Researcher.objects.get(pk=pk)
        ccf.reclusterBatch(r)
    finally:
        r.update_stats()
        update_researcher_task(r, None)


@shared_task(name='fetch_dois_for_researcher')
def fetch_dois_for_researcher(pk):
    researcher = Researcher.objects.get(pk=pk)
    return fetch_publications(researcher)

@shared_task(name='change_publisher_oa_status')
def change_publisher_oa_status(pk, status):
    publisher = Publisher.objects.get(pk=pk)
    publisher.change_oa_status(status)
    publisher.update_stats()

@shared_task(name='consolidate_paper')
@run_only_once('consolidate_paper', keys=['pk'], timeout=1*60)
def consolidate_paper(pk):
    p = None
    try:
        p = Paper.objects.get(pk=pk)
        abstract = p.abstract or ''
        for pub in p.publication_set.all():
            pub = consolidate_publication(pub)
            if pub.abstract and len(pub.abstract) > len(abstract):
                abstract = pub.abstract
                break
    except Paper.DoesNotExist:
        print "consolidate_paper: unknown paper %d" % pk
    finally:
        if p is not None:
            p.task = None
            p.save(update_fields=['task'])



@shared_task(name='update_all_stats')
@run_only_once('refresh_stats', timeout=3*60)
def update_all_stats():
    """
    Updates the stats for every model using them
    """
    AccessStatistics.update_all_stats(PaperWorld)
    AccessStatistics.update_all_stats(Publisher)
    AccessStatistics.update_all_stats(Journal)
    AccessStatistics.update_all_stats(Researcher)
    AccessStatistics.update_all_stats(Institution)
    AccessStatistics.update_all_stats(Department)

@shared_task(name='update_all_stats_but_researchers')
@run_only_once('refresh_stats', timeout=3*60)
def update_all_stats_but_researchers():
    """
    Updates the stats for every model using them
    """
    AccessStatistics.update_all_stats(PaperWorld)
    AccessStatistics.update_all_stats(Publisher)
    AccessStatistics.update_all_stats(Journal)
    AccessStatistics.update_all_stats(Institution)
    AccessStatistics.update_all_stats(Department)


