# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist

from papers.utils import to_plain_name, create_paper_fingerprint
from papers.errors import MetadataSourceException
from papers.models import *
from papers.doi import to_doi
from papers.crossref import fetch_metadata_by_DOI
from papers.romeo import fetch_journal

def lookup_name(author_name):
    first_name = author_name[0]
    last_name = author_name[1]
    name = Name.objects.filter(first__iexact=first_name, last__iexact=last_name).first()
    if name:
        return name
    name = Name(first=first_name, last=last_name)
    name.save()
    return name

def get_or_create_paper(title, author_names, year, doi=None):
    # If a DOI is present, first look up using it
    if doi:
        matches = Publication.objects.filter(doi__exact=doi)
        if matches:
            return matches[0].paper

    if not title or not author_names or not year:
        raise ValueError("A title, year and authors have to be provided to create a paper.")

    # Otherwise look up the fingerprint
    plain_names = map(to_plain_name, author_names)
    fp = create_paper_fingerprint(title, plain_names)
    matches = Paper.objects.filter(fingerprint__exact=fp)

    p = None
    if matches:
        p = matches[0]
    else:
        p = Paper(title=title,year=year,fingerprint=fp)
        p.save()
        for author_name in author_names:
            a = Author(name=author_name, paper=p)
            a.save()

    if doi:
        try:
            metadata = fetch_metadata_by_DOI(doi)
            create_publication(p, metadata)
        except MetadataSourceException as e:
            print "Warning, metadata source exception while fetching DOI "+doi+":\n"+unicode(e)
            pass

    return p

# Create a Publication entry based on the DOI metadata
def create_publication(paper, metadata):
    if not 'container-title' in metadata or not metadata['container-title']:
        return
    title = metadata['container-title']
    volume = metadata.get('volume',None)
    pages = metadata.get('page',None)
    issue = metadata.get('issue',None)
    date_dict = metadata.get('issued',dict())
    date = '-'.join(map(str,date_dict.get('date-parts',[[]])[0]))
    publisher = metadata.get('publisher', None)
    doi = to_doi(metadata.get('DOI',None))
    pubtype = 'article'

    # Lookup journal
    journal = fetch_journal({'jtitle':title})
    # TODO use the "publisher" info ?

    pub = Publication(title=title, issue=issue, volume=volume,
            date=date, paper=paper, pages=pages,
            doi=doi, pubtype=pubtype, publisher=publisher,
            journal=journal)
    pub.save()
    return pub


