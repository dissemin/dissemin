# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
import re

from papers.utils import to_plain_name, create_paper_fingerprint, normalize_name_words, iunaccent, remove_diacritics
from papers.errors import MetadataSourceException
from papers.models import *
from papers.doi import to_doi
from papers.crossref import fetch_metadata_by_DOI
from papers.romeo import fetch_journal

# Name managemement: heuristics to separate a name into (first,last)
comma_re = re.compile(r',+')
space_re = re.compile(r'\s+')
initial_re = re.compile(r'(^|\W)\w(\W|$)')
lowercase_re = re.compile(r'[a-z]')

# Does this string contain a name initial?
def contains_initials(s):
    return initial_re.search(iunaccent(s)) != None
# Is this word fully capitalized?
def is_fully_capitalized(s):
    return lowercase_re.search(remove_diacritics(s)) == None
# Split a word according to a predicate
def predsplit_forward(predicate, words):
    first = []
    last = []
    predHolds = True
    for i in range(len(words)):
        if predicate(i) and predHolds:
            first.append(words[i])
        else:
            predHolds = False
            last.append(words[i])
    return (first,last)
# The same, but backwards
def predsplit_backwards(predicate, words):
    first = []
    last = []
    predHolds = True
    for i in reversed(range(len(words))):
        if predicate(i) and predHolds:
            last.insert(0, words[i])
        else:
            predHolds = False
            first.insert(0, words[i])
    return (first,last)

def parse_comma_name(name):
    """
    Parse an name of the form "Last name, First name" to (first name, last name)
    Tries to do something reasonable if there is no comma.
    """
    if ',' in name:
        name = comma_re.sub(',',name)
        idx = name.find(',')
        last_name = name[:idx]
        first_name = name[(idx+1):]
    else:
        # TODO: there is probably a better way to parse names such as "Colin de la Higuera"
        # list of "particle words" such as "de, von, van, du" ?
        # That would be europe-centric though...
        words = space_re.split(name)
        if not words:
            return ('','')

        # Search for initials in the words
        initial = map(contains_initials, words)
        capitalized = map(is_fully_capitalized, words)

        # CASE 1: the first word is capitalized but not all of them are
        # we assume that it is the first word of the last name
        if not initial[0] and capitalized[0] and not all(capitalized):
            (last,first) = predsplit_forward(
                    (lambda i: capitalized[i] and not initial[i]),
                    words)
            

        # CASE 2: the last word is capitalized but not all of them are
        # we assume that it is the last word of the last name
        elif not initial[-1] and capitalized[-1] and not all(capitalized):
            (first,last) = predsplit_backwards(
                    (lambda i: capitalized[i] and not initial[i]),
                    words)

        # CASE 3: the first word is an initial
        elif initial[0]:
            (first,last) = predsplit_forward(
                    (lambda i: initial[i]),
                    words)

        # CASE 4: the last word is an initial
        # this is trickier, we know that the last name comes first
        # but we don't really know where it stops.
        # For simplicity we assume that all the words in the first
        # name are initials
        elif initial[-1]:
            (last,first) = predsplit_backwards(
                    (lambda i: initial[i]),
                    words)

        # CASE 5: there are initials in the name, but neither
        # at the beginning nor at the end
        elif True in initial:
            last_initial_idx = None
            for i in range(len(words)):
                if initial[i]:
                    last_initial_idx = i
            first = words[:last_initial_idx+1]
            last = words[last_initial_idx+1:]

        # CASE 6: we have no clue
        # We simply cut roughly in the middle !
        else:
            cut_idx = len(words)/2
            if len(words) == 3:
                cut_idx = 2
            first = words[:cut_idx]
            last = words[cut_idx:]
            
        first_name = ' '.join(first)
        last_name = ' '.join(last)

    first_name = first_name.strip()
    last_name = last_name.strip()
    first_name = normalize_name_words(first_name)
    last_name = normalize_name_words(last_name)

    if not last_name:
        first_name, last_name = last_name, first_name

    return (first_name,last_name)

def lookup_name(author_name):
    first_name = author_name[0]
    last_name = author_name[1]
    full_name = first_name+' '+last_name
    full_name = full_name.strip()
    normalized = iunaccent(full_name)
    name = Name.objects.filter(full=normalized).first()
    if name:
        return name
    name = Name.create(first_name,last_name)
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

# Merges the second paper into the first one
def merge_papers(first, second):
    # TODO What if the authors are not the same?
    # We should merge the list of authors, so that the order is preserved

    if first.pk == second.pk:
        return
    
    OaiRecord.objects.filter(about=second.pk).update(about=first.pk)
    Publication.objects.filter(paper=second.pk).update(paper=first.pk)
    second.delete()
    first.update_oa_status()
    first.update_pdf_url()


# Create a Publication entry based on the DOI metadata
def create_publication(paper, metadata):
    if not metadata:
        return
    if not 'container-title' in metadata or not metadata['container-title']:
        return
    doi = to_doi(metadata.get('DOI',None))
    # Test first if there is no publication with this new DOI
    matches = Publication.objects.filter(doi__exact=doi)
    if matches:
        return matches[0]

    title = metadata['container-title']
    issn = metadata.get('ISSN',None)
    if issn and type(issn) == type([]):
        issn = issn[0] # TODO pass all the ISSN to the RoMEO interface
    volume = metadata.get('volume',None)
    pages = metadata.get('page',None)
    issue = metadata.get('issue',None)
    date_dict = metadata.get('issued',dict())
    date = '-'.join(map(str,date_dict.get('date-parts',[[]])[0])) # TODO this is horribly ugly
    # for instance it outputs dates like 2014-2-3
    publisher = metadata.get('publisher', None)
    pubtype = 'article'

    # Lookup journal
    search_terms = {'jtitle':title}
    if issn:
        search_terms['issn'] = issn
    journal = fetch_journal(search_terms)
    # TODO use the "publisher" info ?


    pub = Publication(title=title, issue=issue, volume=volume,
            date=date, paper=paper, pages=pages,
            doi=doi, pubtype=pubtype, publisher=publisher,
            journal=journal)
    pub.save()
    paper.update_oa_status()
    paper.update_pdf_url()
    return pub


