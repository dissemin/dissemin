# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.utils import to_plain_author, create_paper_fingerprint
from papers.models import Researcher, Paper, Author, DoiRecord, Publication

def lookup_author(author):
    first_name = author[0]
    last_name = author[1]
    results = Researcher.objects.filter(first_name__iexact=first_name,last_name__iexact=last_name)
    if len(results) > 0:
        return results[0]
    else:
        return author

def get_or_create_paper(title, authors, year, doi):
    # If a DOI is present, first look up using it
    if doi:
        matches = DoiRecord.objects.filter(doi__exact=doi)
        if matches:
            return matches[0].about

    if not title or not authors or not year:
        raise ValueError("A title, year and authors have to be provided to create a paper.")

    # Otherwise look up the fingerprint
    plain_authors = map(to_plain_author, authors)
    fp = create_paper_fingerprint(title, plain_authors)
    matches = Paper.objects.filter(fingerprint__exact=fp)
    if matches:
        p = matches[0]
        # Add the DOI to the existing paper
        if doi:
            d = DoiRecord(doi=doi, about=p)
            d.save()
        return p

    p = Paper(title=title,year=year,fingerprint=fp)
    p.save()
    for author in authors:
        if type(author) == type(()):
            a = Author(first_name=author[0],last_name=author[1],paper=p)
        else:
            a = Author(first_name=author.first_name,
                       last_name=author.last_name,
                       paper=p,
                       researcher=author)
        a.save()

    if doi:
        d = DoiRecord(doi=doi, about=p)
        d.save()

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

    pub = Publication(title=title, issue=issue, volume=volume, date=date, paper=paper, pages=pages)
    pub.save()
    return pub


