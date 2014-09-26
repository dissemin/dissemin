# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.utils import to_plain_author, create_paper_fingerprint
from papers.models import Researcher, Paper, Author, DoiRecord

def lookup_author(author):
    first_name = author[0]
    last_name = author[1]
    results = Researcher.objects.filter(first_name__iexact=first_name,last_name__iexact=last_name)
    if len(results) > 0:
        return results[0]
    else:
        return author

def get_or_create_paper(title, authors, doi):
    # If a DOI is present, first look up using it
    if doi:
        matches = DoiRecord.objects.filter(doi__exact=doi)
        if matches:
            return matches[0].about

    # Otherwise look up the fingerprint
    plain_authors = map(to_plain_author, authors)
    fp = create_paper_fingerprint(title, plain_authors)
    matches = Paper.objects.filter(fingerprint__exact=fp)
    if matches:
        p = matches[0]
        # Add the DOI to the existing paper
        if doi:
            d = DoiRecord(doi=doi, about=p) # TODO fetch this DOI ?
            d.save()
        return p

    p = Paper(title=title)
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
        d = DoiRecord(doi=doi, about=p) # TODO fetch this DOI ?
        d.save()

    return p

