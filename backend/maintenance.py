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

"""
This module contains functions that are not normally needed
to run the platform, but that can be useful during development,
or to cleanup various things in the database.

These functions are not integrated in the rest of the platform,
so running them involves starting a Django shell ("python manage.py shell"),
importing this module and running the function manually.
"""

from __future__ import unicode_literals

from papers.models import *
from publishers.models import *
import backend.crossref
from papers.utils import sanitize_html
from backend.romeo import fetch_publisher
from backend.tasks import change_publisher_oa_status
from backend.crossref import fetch_metadata_by_DOI, is_oa_license
from backend.name_cache import name_lookup_cache
from time import sleep
from lxml.html import fromstring
from collections import defaultdict
from django.db.models import Q, Prefetch
from django.db import DatabaseError
from papers.errors import MetadataSourceException

def cleanup_researchers():
    """
    Deletes all the researchers who have not authored any paper.
    """
    deleted_count = 0
    for p in Researcher.objects.all():
        nb_papers = Paper.objects.filter(author__researcher=p).count()
        if not nb_papers:
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" researchers"


def cleanup_names(dry_run = False):
    """
    Deletes all the names that are not present in any paper.
    """
    deleted_count = 0
    for n in Name.objects.all():
        if NameVariant.objects.filter(name=n).count() == 0:
            nb_papers = Author.objects.filter(name=n).count()
            if not nb_papers:
                deleted_count += 1
                if not dry_run:
                    n.delete()
    print "Deleted "+str(deleted_count)+" names"

def merge_names(fro,to):
    """
    Merges the name object 'fro' into 'to
    """
    Researcher.objects.filter(name_id=fro.id).update(name_id=to.id)
    NameVariant.objects.filter(name_id=fro.id).update(name_id=to.id)
    Author.objects.filter(name_id=fro.id).update(name_id=to.id)
    fro.delete()

def update_paper_statuses():
    """
    Should only be run if something went wrong,
    the backend is supposed to update the fields by itself
    """
    papers = Paper.objects.all()
    for p in papers:
        p.update_availability()

def cleanup_titles():
    """
    Run HTML sanitizing on all the titles of the papers
    (this is normally done on creation of the papers, but
    not for old dumps of the database)
    """
    papers = Paper.objects.all()
    for p in papers:
        p.title = sanitize_html(p.title)
        p.save(update_fields=['title'])

def cleanup_abstracts():
    """
    Run HTML sanitizing on the abstracts
    (this is normally done on creation of the papers, but
    not for old dumps of the database)
    """
    for p in Publication.objects.all():
        if p.abstract:
            new_abstract = sanitize_html(p.abstract)
            if new_abstract != p.abstract:
                p.abstract = new_abstract
                p.save()
    for p in OaiRecord.objects.all():
        if p.description:
            new_abstract = sanitize_html(p.description)
            if new_abstract != p.description:
                p.description = new_abstract
                p.save()

def recompute_fingerprints():
    """
    Recomputes the fingerprints of all papers, merging
    those who end up having the same fingerprint
    """
    merged = 0
    pc = Paper.objects.all().count()
    for idx, p in enumerate(Paper.objects.all()):
        if idx % 100 == 0:
            print idx
        p.fingerprint = 'blah'
        match = p.recompute_fingerprint_and_merge_if_needed()
        if match is not None:
            merged += 1
    print "%d papers merged" % merged

def find_collisions():
    """
    Recomputes all the fingerprints and reports those which would be
    merged by recompute_fingerprints()
    """
    dct = defaultdict(set)
    for p in Paper.objects.all():
        fp = p.new_fingerprint()
        dct[fp].add(p)

    for fp, s in dct.items():
        if len(s) > 1:
            first = True
            for paper in s:
                if first:
                    first = False
                    print "### "+paper.plain_fingerprint()
                print paper.title
                print paper.bare_author_names()

def create_publisher_aliases(erase_existing=True):
    # TODO: this might be more efficient with aggregates?
    counts = defaultdict(int)
    for p in Publication.objects.all():
        if p.publisher_id:
            pair = (p.publisher_name,p.publisher_id)
            counts[pair] += 1

    if erase_existing:
        AliasPublisher.objects.all().delete()

    for (name,pk) in counts:
        if not erase_existing:
            alias = AliasPublisher.objects.get_or_create(name=name,publisher_id=pk)
        else:
            alias = AliasPublisher(name=name,publisher_id=pk)
        alias.count = counts[(name,pk)]
        alias.save()

def refetch_publishers():
    """
    Tries to assign publishers to Publications without Journals
    """
    for p in Publication.objects.filter(publisher__isnull=True):
        publisher = fetch_publisher(p.publisher_name)
        if publisher:
            p.publisher = publisher
            p.save(update_fields=['publisher'])
            p.paper.update_availability()

def refetch_containers():
    """
    Tries to assign containers to Publications without containers
    """
    # TODO 
    for p in Publication.objects.filter(container__isnull=True):
        metadata = backend.crossref.fetch_metadata_by_DOI(p.doi)
        if metadata is None:
            continue
        p.container = metadata.get('container-title')
        if p.container:
            p.save()

def hide_unattributed_papers():
    """
    Changes the visibility of papers based on whether they are attributed to a researcher or
    not (only VISIBLE <-> NOT_RELEVANT)
    """
    qset = Paper.objects.filter(Q(visibility='VISIBLE') | Q(visibility='NOT_RELEVANT'))
    count = qset.count()
    cursor = 0
    chunksize = 100
    while cursor < count:
        for p in qset[cursor:cursor+chunksize].prefetch_related(
                Prefetch('author_set', to_attr='authors')):
            p.update_visibility()
        cursor += chunksize


def recompute_publisher_policies():
    """
    Recomputes the publisher policy according to some possibly new criteria
    """
    for p in Publisher.objects.all():
        change_publisher_oa_status(p.pk, p.classify_oa_status())


def prune_name_lookup_cache(threshold):
    """
    Prunes the name lookup cache (removes names which are not looked up often)
    """
    name_lookup_cache.prune(threshold)


def refetch_doi_availability():
    """
    Refetches DOI metadata for all publications
    """
    def fetch_oa(doi):
        metadata = fetch_metadata_by_DOI(doi)
        if metadata is None:
            return False
        licenses = set([(license or {}).get('URL') for license in metadata.get('license', [])])
        return any(map(is_oa_license, licenses))

    for p in Publication.objects.filter(pdf_url__isnull=True):
        if not p.doi:
            continue
        try:
            if not p.pdf_url and (p.oa_status() == 'OA' or fetch_oa(p.doi)):
                print "Updating DOI "+p.doi
                p.pdf_url = 'http://dx.doi.org/'+p.doi
                p.save(update_fields=['pdf_url'])
                p.paper.update_availability()
        except MetadataSourceException as e:
            continue


