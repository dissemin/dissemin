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

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db import DataError
import re

from papers.utils import create_paper_fingerprint, date_from_dateparts, sanitize_html
from papers.errors import MetadataSourceException
from papers.models import *
from papers.doi import to_doi
from papers.name import to_plain_name, parse_comma_name

from publishers.models import AliasPublisher

import backend.crossref
from backend.romeo import fetch_journal, fetch_publisher
from backend.globals import *
from backend.utils import maybe_recapitalize_title

# TODO: this could be a method of ClusteringContextFactory ?
def get_or_create_paper(title, author_names, pubdate, doi=None, visibility='VISIBLE'):
    """
    Creates a paper if it is not already present.
    The clustering algorithm is run to decide what authors should be 
    attributed to the paper.

    :param title: The title of the paper (as a string). If it is too long for the database,
                  ValueError is raised.
    :param author_names: The ordered list of author names, as Name objects.
    :param pubdate: The publication date, as a python date object
    :param doi: If provided, also fetch metadata from CrossRef based on this DOI and
                create the relevant publication.
    :param visibility: The visibility of the paper if it is created. If another paper
                exists, the visibility will be set to the maximum of the two possible
                visibilities.
    """
    try:
        return _get_or_create_paper(title, author_names, pubdate, doi, visibility)
    except DataError as e:
        raise ValueError('Invalid paper, does not fit in the database schema:\n'+unicode(e))

def _get_or_create_paper(title, author_names, pubdate, doi, visibility):
    plain_names = map(to_plain_name, author_names)

    def upgrade_visibility(paper):
        if visibility == 'VISIBLE' and paper.visibility == 'CANDIDATE':
            paper.visibility = 'VISIBLE'
            paper.save(update_fields=['visibility'])
        paper.update_author_names(plain_names)
        return paper

    # If a DOI is present, first look it up
    if doi:
        matches = Publication.objects.filter(doi__exact=doi)
        if matches:
            return upgrade_visibility(matches[0].paper)

    if not title or not author_names or not pubdate:
        raise ValueError("A title, pubdate and authors have to be provided to create a paper.")

    title = sanitize_html(title)
    title = maybe_recapitalize_title(title)

    # Otherwise look up the fingerprint
    fp = create_paper_fingerprint(title, plain_names, pubdate.year)
    matches = Paper.objects.filter(fingerprint__exact=fp)

    p = None
    if matches:
        p = upgrade_visibility(matches[0])
    else:
        p = Paper(title=title,
                pubdate=pubdate,
                doctype='other',
                year=pubdate.year,
                fingerprint=fp,
                visibility=visibility)
        p.save()
        for idx, author_name in enumerate(author_names):
            author_name.save_if_not_saved()
            a = Author(name=author_name, paper=p, position=idx)
            a.save()
            if author_name.is_known:
                clustering_context_factory.clusterAuthorLater(a)

    if doi:
        try:
            metadata = backend.crossref.fetch_metadata_by_DOI(doi)
            create_publication(p, metadata)
        except MetadataSourceException as e:
            print "Warning, metadata source exception while fetching DOI "+doi+":\n"+unicode(e)
            pass
    return p


CROSSREF_PUBTYPE_ALIASES = {
        'article':'journal-article',
        }

def create_publication(paper, metadata):
    """
    Creates a Publication entry based on the DOI metadata (as returned by the JSON format
    from CrossRef).

    :param paper: the paper the publication object refers to
    :param metadata: the CrossRef metadata (parsed from JSON)
    :return: None if the metadata is invalid or the data does not fit in the database schema.
    """
    try:
        return _create_publication(paper, metadata)
    except DataError:
        pass

def _create_publication(paper, metadata):
    if not metadata:
        return
    if not 'container-title' in metadata or not metadata['container-title']:
        return
    doi = to_doi(metadata.get('DOI',None))
    # Test first if there is no publication with this new DOI
    matches = Publication.objects.filter(doi__exact=doi)
    if matches:
        return matches[0]

    title = metadata['container-title'][:512]
    issn = metadata.get('ISSN',None)
    if issn and type(issn) == type([]):
        issn = issn[0] # TODO pass all the ISSN to the RoMEO interface
    volume = metadata.get('volume',None)
    pages = metadata.get('page',None)
    issue = metadata.get('issue',None)
    date_dict = metadata.get('issued',dict())
    pubdate = None
    if 'date-parts' in date_dict:
        dateparts = date_dict.get('date-parts')[0]
        pubdate = date_from_dateparts(dateparts)
    # for instance it outputs dates like 2014-2-3
    publisher_name = metadata.get('publisher', None)
    if publisher_name:
        publisher_name = publisher_name[:512]

    pubtype = metadata.get('type','unknown')
    pubtype = CROSSREF_PUBTYPE_ALIASES.get(pubtype, pubtype)

    # Lookup journal
    search_terms = {'jtitle':title}
    if issn:
        search_terms['issn'] = issn
    journal = fetch_journal(search_terms)

    publisher = None
    if journal:
        publisher = journal.publisher
        AliasPublisher.increment(publisher_name, journal.publisher)
    else:
        publisher = fetch_publisher(publisher_name)

    pub = Publication(title=title, issue=issue, volume=volume,
            pubdate=pubdate, paper=paper, pages=pages,
            doi=doi, pubtype=pubtype, publisher_name=publisher_name,
            journal=journal, publisher=publisher)
    pub.save()
    cur_pubdate = paper.pubdate
    if type(cur_pubdate) != type(pubdate):
        cur_pubdate = cur_pubdate.date()
    if pubdate and pubdate > cur_pubdate:
        paper.pubdate = pubdate
    paper.update_availability()
    return pub


