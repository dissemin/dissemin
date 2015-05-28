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

from __future__ import unicode_literals

from papers.models import *
from papers.utils import sanitize_html, create_paper_fingerprint
from backend.romeo import fetch_publisher
from time import sleep
from collections import defaultdict
from django.db.models import Q, Prefetch
from django.db import DatabaseError

def cleanup_papers():
    """
    Deletes all the papers where none of the authors have been identified
    as a known researcher.
    TODO: write another version focusing on the last name only.
    """
    deleted_count = 0
    for p in Paper.objects.all().select_related('author'):
        sleep(0.1)
        researcher_found = False
        for a in p.author_set.all():
            if a.researcher:
                researcher_found = True
                break
        if not researcher_found:
            print "Deleting paper id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" papers"


def cleanup_researchers():
    """
    Deletes all the researchers who have not authored any paper.
    """
    deleted_count = 0
    for p in Researcher.objects.all():
        nb_papers = Paper.objects.filter(author__researcher=p).count()
        if not nb_papers:
            print "Deleting researcher id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" researchers"


def cleanup_names(dry_run = False):
    """
    Deletes all the names that are not present in any paper.
    """
    deleted_count = 0
    for n in Name.objects.all():
        if not n.researcher:
            nb_papers = Author.objects.filter(name=n).count()
            if not nb_papers:
                print "Deleting name id "+str(n.pk)+": "+unicode(n)
                deleted_count += 1
                if not dry_run:
                    n.delete()
    print "Deleted "+str(deleted_count)+" names"

def add_names_to_variants():
    """
    Ensures the name of each researcher is in its other_names set
    """
    for r in Researcher.objects.all():
        r.name_variants.add(r.name)

def merge_names(fro,to):
    """
    Merges the name object 'fro' into 'to
    """
    Researcher.objects.filter(name_id=fro.id).update(name_id=to.id)
    ResearcherVariants = Researcher.name_variants.through
    ResearcherVariants.objects.filter(name_id=fro.id).update(name_id=to.id)
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

def update_all_stats():
    """
    Updates the stats for every model using them
    """
    AccessStatistics.update_all_stats(Department)
    AccessStatistics.update_all_stats(Publisher)
    AccessStatistics.update_all_stats(Journal)
    AccessStatistics.update_all_stats(Researcher)

def recompute_fingerprints():
    """
    Recomputes the fingerprints of all papers, merging
    those who end up having the same fingerprint
    """
    merged = 0
    for p in Paper.objects.all():
        authors = [(a.name.first,a.name.last) for a in p.author_set.all().select_related('name')]
        new_fp = create_paper_fingerprint(p.title, authors)
        if new_fp != p.fingerprint:
            matching = list(Paper.objects.filter(fingerprint=new_fp))
            if matching:
                p.merge(matching[0])
                merged += 1
            else:
                p.fingerprint = new_fp
                try:
                    p.save(update_fields=['fingerprint'])
                except DatabaseError as e:
                    pass
    print "%d papers merged" % merged

def journal_to_publisher():
    """
    Sets the "publisher" field of publications where the "journal" field
    is not empty.
    """
    # TODO: is there a more efficient way to do this with updates?
    for publi in Publication.objects.filter(journal__isnull=False).select_related('journal'):
        publi.publisher_id = publi.journal.publisher_id
        publi.save(update_fields=['publisher'])

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

