# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""
This module defines *bare* versions of the regular models: these
are classes whose instances do not correspond to an object in the database.
They are only stored in memory. This is useful for the API, where lookups are done online,
without name ambiguity resolution.
"""

import hashlib, re
from urllib import urlencode, quote # for the Google Scholar and CORE link

from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from django.core.exceptions import ObjectDoesNotExist

from papers.utils import *
from statistics.models import COMBINED_STATUS_CHOICES, PDF_STATUS_CHOICES, STATUS_CHOICES_HELPTEXT
from publishers.models import Publisher, Journal, OA_STATUS_CHOICES, OA_STATUS_PREFERENCE, DummyPublisher


VISIBILITY_CHOICES = [('VISIBLE', _('Visible')),
                      ('CANDIDATE', _('Candidate')),
                      ('NOT_RELEVANT', _('Not relevant')),
                      ('DELETED', _('Deleted')),
                      ]

PAPER_TYPE_CHOICES = [
   ('journal-article', _('Journal article')),
   ('proceedings-article', _('Proceedings article')),
   ('book-chapter', _('Book chapter')),
   ('book', _('Book')),
   ('journal-issue', _('Journal issue')),
   ('proceedings', _('Proceedings')),
   ('reference-entry', _('Entry')),
   ('poster', _('Poster')),
   ('report', _('Report')),
   ('thesis', _('Thesis')),
   ('dataset', _('Dataset')),
   ('preprint', _('Preprint')),
   ('other', _('Other document')),
   ]

PAPER_TYPE_PREFERENCE = [x for (x,y) in PAPER_TYPE_CHOICES]

MAX_NAME_LENGTH = 256

class BarePaper(object):
    """
    This class is the bare analogue to :class:`Paper`. Its authors are
    lists of :class:`BareName`, and its publications and OAI records are also bare.
    """

    #! The title of the paper
    title = None
    #! The fingerprint (robust version of the title, authors and year)
    fingerprint = None
    #! The publication date
    pubdate = None
    #! The document type
    doctype = None
    #! The OA status
    oa_status = None
    #! The url where we think the full text is available
    pdf_url = None
    #! Visibility
    visibility = None

    #! The authors: a list of :class:`BareName`
    bare_authors = []
    #! The publications associated with this paper: a list of :class:`BarePublication`
    bare_publications = []
    #! The OAI records associated with this paper: a list of :class:`BarePublication`
    bare_oairecords = []

    # Number of `uninteresting` authors
    nb_remaining_authors = None

    ### Properties to be reimplemented by non-bare Paper ###
    @property
    def authors(self):
        """
        The list of authors. They are bare in :class:`BarePaper`. In
        other implementations, they can be arbitrary iterables of subclasses
        of :class:`BareAuthor`.
        They are sorted in their natural order on paper.
        """
        return self.bare_authors

    @property
    def publications(self):
        """
        The list of publications associated with this paper. They
        can be arbitrary iterables of subclasses of :class:`BarePublication`.
        """
        return self.bare_publications

    @property
    def oairecords(self):
        """
        The list of OAI records associated with this paper. It can
        be arbitrary iterables of subclasses of :class:`BareOaiRecord`.
        """
        return self.bare_oairecords

    ### Generic properties that should not need to be reimplemented ###
    @property
    def year(self):
        """
        Year of publication of the paper.
        """
        return self.pubdate.year

    # OAI records -----------------

    @cached_property
    def sorted_oai_records(self):
        """
        OAI records sorted by decreasing order of priority
        (lower priority means poorer overall quality of the source).
        """
        # Ordered in Python because the list of records is typically quite
        # small (less than 10 items)
        return sorted(self.oairecords, key=lambda r: -r.priority)

    @cached_property
    def prioritary_oai_records(self):
        """
        OAI records from custom sources we trust (positive priority)
        """
        # Filtered in Python because the list of records is typically quite
        # small (less than 10 items)
        return filter(lambda r: r.priority > 0, self.sorted_oai_records)

    @property
    def unique_prioritary_oai_records(self):
        """
        OAI records from sources we trust, with unique source.
        """
        seen_sources = set()
        for record in self.prioritary_oai_records:
            if record.source_id not in seen_sources:
                seen_sources.add(record.source_id)
                yield record

    # Authors ------------------------

    def author_names(self):
        """
        The list of Name instances of the authors
        """
        return [a.name for a in self.authors]

    def bare_author_names(self):
        """
        The list of name pairs (first,last) of the authors
        """
        return [(name.first,name.last) for name in self.author_names()]

    @property
    def author_count(self):
        """
        Number of authors.
        """
        return len(self.authors)

    @property
    def has_many_authors(self):
        """
        When the paper has more than 15 authors (arbitrary threshold)
        """
        return self.author_count > 15

    @cached_property
    def interesting_authors(self):
        """
        The list of authors to display when the complete list is too long.
        We display first the authors whose names are known, and then a few ones
        who are unknown.
        """
        lst = (filter(lambda a: a.name.best_confidence > 0, self.authors)+filter(
                      lambda a: a.name.best_confidence == 0, self.authors)[:3])[:15]
        self.nb_remaining_authors = self.author_count - len(lst)
        return lst

    def displayed_authors(self):
        """
        Returns the full list of authors if there are not too many of them,
        otherwise returns only the interesting_authors()
        """
        if self.has_many_authors:
            return self.interesting_authors
        else:
            return self.authors

    # Publications ---------------------------------------------
    
    def first_publications(self):
        """
        The list of the 3 first publications associated with this paper
        (in most cases, that should return *all* publications, but in some nasty cases
        many publications end up merged, and it is not very elegant to show all of them
        to the users).
        """
        return self.publications[:3]

    def publications_with_unique_publisher(self):
        """
        Iterable of publications where subsequent publications with
        the same publisher are removed.
        """
        seen_publishers = set()
        for publication in self.publications:
            if publication.publisher_id and publication.publisher_id not in seen_publishers:
                seen_publishers.add(publication.publisher_id)
                yield publication
            elif publication.publisher_name not in seen_publishers:
                seen_publishers.add(publication.publisher_name)
                yield publication

    def publisher(self):
        """
        Returns the first publisher we can find for this paper, otherwise
        a :class:`DummyPublisher`
        """
        for publication in self.publications:
            return publication.publisher_or_default()
        return DummyPublisher()


    # Visibility ------------------------------------------------
    @property
    def toggled_visibility(self):
        if self.visibility == 'VISIBLE':
            return 2 # NOT RELEVANT
        return 0 # VISIBLE

    @property
    def visibility_code(self):
        return index_of(self.visibility, VISIBILITY_CHOICES)

    # Fingerprint -----------------------------------------------
    def plain_fingerprint(self, verbose=False):
        """
        Debugging function to display the plain fingerprint
        """
        fp = create_paper_plain_fingerprint(self.title, self.bare_author_names(), self.year)
        if verbose:
            print fp
        return fp

    def new_fingerprint(self, verbose=False):
        """
        The fingerprint of the paper, taking into account the changes
        that may have occured since the last computation of the fingerprint.
        This does not update the `fingerprint` field, just computes its candidate value.
        """
        buf = self.plain_fingerprint(verbose)
        m = hashlib.md5()
        m.update(buf)
        return m.hexdigest()

    # Abstract -------------------------------------------------
    @cached_property
    def abstract(self):
        for rec in self.publication_set.all():
            if rec.abstract:
                return rec.abstract
        best_abstract = ''
        for rec in self.oairecord_set.all():
            if rec.description and len(rec.description) > len(best_abstract):
                best_abstract = rec.description
        return best_abstract


    # Updates ---------------------------------------------------
    def update_availability(self):
        """
        Updates the :class:`BarePaper`'s own `pdf_url` field
        based on its sources (both :class:`BarePublication` and :class:`BareOaiRecord`).
        
        This uses a non-trivial logic, hence it is useful to keep this result cached
        in the database row.
        """
        self.pdf_url = None
        publis = self.publications
        oa_idx = len(OA_STATUS_PREFERENCE)-1
        type_idx = len(PAPER_TYPE_PREFERENCE)-1
        source_found = False

        if self.doctype in PAPER_TYPE_PREFERENCE:
            type_idx = PAPER_TYPE_PREFERENCE.index(self.doctype)
        for publi in publis:
            # OA status
            cur_status = publi.oa_status()
            try:
                idx = OA_STATUS_PREFERENCE.index(cur_status)
            except ValueError:
                idx = len(OA_STATUS_PREFERENCE)
            oa_idx = min(idx, oa_idx)
            if OA_STATUS_CHOICES[oa_idx][0] == 'OA':
                self.pdf_url = publi.pdf_url or publi.splash_url()

            # Pub type
            cur_type = publi.pubtype
            try:
                idx = PAPER_TYPE_PREFERENCE.index(cur_type)
            except ValueError:
                idx = len(PAPER_TYPE_PREFERENCE)
            type_idx = min(idx, type_idx)

            source_found = True

        self.oa_status = OA_STATUS_CHOICES[oa_idx][0]
        if not self.pdf_url:
            records = list(self.oairecords)
            matches = sorted(self.oairecords, key=(lambda r: (-r.source.oa,-r.source.priority)))
            self.pdf_url = None
            for m in matches:
                if not self.pdf_url:
                    self.pdf_url = m.pdf_url

                if m.source.oa:
                    self.oa_status = 'OA'
                    if not self.pdf_url:
                        self.pdf_url = m.splash_url

                if m.pubtype in PAPER_TYPE_PREFERENCE:
                    new_idx = PAPER_TYPE_PREFERENCE.index(m.pubtype)
                    type_idx = min(new_idx, type_idx)

                source_found = True

        # If this paper is not associated with any source, do not display it
        # This happens when creating the associated OaiRecord or Publication
        # failed due to some missing information.
        if not source_found:
            self.visibility = 'CANDIDATE'

        self.doctype = PAPER_TYPE_PREFERENCE[type_idx]

    def update_visibility(self):
        """
        Updates the visibility of the paper. Only papers with
        known authors should be visible.
        """
        p = self
        if p.visibility != 'VISIBLE' and p.visibility != 'NOT_RELEVANT':
            return
        researcher_found = False
        for a in p.authors:
            if a.researcher_id:
                researcher_found = True
                break
        if researcher_found and p.visibility != 'VISIBLE':
            p.visibility = 'VISIBLE'
            p.save(update_fields=['visibility'])
        elif not researcher_found and p.visibility != 'NOT_RELEVANT':
            p.visibility = 'NOT_RELEVANT'
            p.save(update_fields=['visibility'])

    # Other representations ------------------------------------------
    def __unicode__(self):
        """
        Title of the paper
        """
        return self.title

    def json(self):
        """
        JSON representation of the paper, for dataset dumping purposes
        """
        return remove_nones({
            'title': self.title,
            'type': self.doctype,
            'date': self.pubdate.isoformat(),
            'authors': [a.json() for a in self.authors],
            'publications': [p.json() for p in self.publications],
            'records': [r.json() for r in self.oairecords],
            'pdf_url': self.pdf_url,
            })


    def google_scholar_link(self):
        """
        Link to search for the paper in Google Scholar
        """
        return 'http://scholar.google.com/scholar?'+urlencode({'q':remove_diacritics(self.title)})

    def core_link(self):
        """
        Link to search for the paper in CORE
        """
        return 'http://core.ac.uk/search/'+quote(remove_diacritics(self.title))

    def is_orphan(self):
        """
        When no publication or OAI record is associated with this paper.
        """
        return (len(self.oairecords) + len(self.publications) == 0)

    def citation(self):
        """
        A short citation-like representation of the paper. E.g. Joyal and Street, 1992
        """
        result = ''
        if self.author_count == 1:
            result = self.authors[0].name.last
        elif self.author_count == 2:
            result = "%s and %s" % (
                self.authors[0].name.last,
                self.authors[1].name.last)
        else:
            result = "%s et al." % (
                self.authors[0].name.last)
        result += ', %d' % self.year
        return result

class BareAuthor(object):
    """
    The base class for the author of a paper.
    This holds the name of the author, its position in the authors list,
    and its possible affiliations.
    """
    name = None
    affiliation = None

    @property
    def orcid(self):
        """
        Returns the ORCID associated to this author (if any).
        Note that this can be null even if the author is associated with a researcher
        that has an ORCID.
        """
        return validate_orcid(self.affiliation)


    # Representations -------------------------------
    def __unicode__(self):
        """
        Unicode representation: name of the author
        """
        return unicode(self.name)

    def json(self):
        """
        JSON representation of the author for dataset dumping purposes
        """
        orcid_id = self.orcid
        affiliation = None
        if not orcid_id and self.affiliation:
            affiliation = self.affiliation
        return remove_nones({
                'name':self.name.json(),
                'affiliation':affiliation,
                'orcid':orcid_id,
                })


class BareName(object):
    first = None
    last = None
    full = None

    @property
    def is_known(self):
        """
        Does this name belong to at least one known researcher?
        """
        return True

    @classmethod
    def create(cls, first, last):
        """
        Creates an instance of the Name object without saving it.
        Useful for name lookups where we are not sure we want to
        keep the name in the model.
        """
        instance = cls()
        instance.first = sanitize_html(first[:MAX_NAME_LENGTH].strip())
        instance.last = sanitize_html(last[:MAX_NAME_LENGTH].strip())
        instance.full = iunaccent(instance.first+' '+instance.last)
        return instance

    def __unicode__(self):
        """
        Unicode representation: first name followed by last name
        """
        return '%s %s' % (self.first,self.last)


    def first_letter(self):
        """
        First letter of the last name, for sorting purposes
        """
        return self.last[0]

    def json(self):
        """
        Returns a JSON representation of the name (for dataset dumping purposes)
        """
        return {
                'first':self.first,
                'last':self.last,
               }


class BarePublication(object):
    pubtype = None
    title = None # this is actually the *journal* title
    journal = None # expected to be an actual model instance
    journal_id = None
    container = None
    publisher = None # expected to be an actual model instance
    publisher_id = None 
    publisher_name = None
    issue = None
    volume = None
    pages = None
    pubdate = None
    abstract = None
    doi = None
    pdf_url = None

    def oa_status(self):
        """
        Policy of the publisher for this publication
        """
        if self.pdf_url:
            return 'OA'
        elif self.publisher:
            if self.publisher.oa_status == 'OA' and self.doi:
                self.pdf_url = 'http://dx.doi.org/'+self.doi
                self.save()
            return self.publisher.oa_status
        else:
            return 'UNK'

    def splash_url(self):
        """
        Returns the splash url (the DOI url) for that paper
        (if a DOI is present, otherwise None)
        """
        if self.doi:
            return 'http://dx.doi.org/'+self.doi

    def full_title(self):
        """
        The full title of the journal, otherwise the title present
        in CrossRef's metadata, which might be shorter.
        """
        if self.journal:
            return self.journal.title
        else:
            return self.title

    def publisher_or_default(self):
        """
        Returns the publisher. If the publisher is unknown, 
        returns an instance of :class:`DummyPublisher`.
        """
        if self.publisher_id:
            return self.publisher
        if self.publisher_name:
            return DummyPublisher(self.publisher_name)
        return DummyPublisher()

    def __unicode__(self):
        """
        Title of the publication, followed by the details of the bibliographic reference.
        """
        return self.title

    def json(self):
        """
        JSON representation of the publication, for dataset dumping purposes
        """
        result = {
                'doi':self.doi,
                'pdf_url':self.pdf_url,
                'type':self.pubtype,
                'publisher':self.publisher_name,
                'journal':self.full_title(),
                'container':self.container,
                'issue':self.issue,
                'volume':self.volume,
                'pages':self.pages,
                'abstract':self.abstract,
               }
        if self.publisher:
            result['policy'] = self.publisher.json()
        if self.journal:
            result['issn'] = self.journal.issn
        return remove_nones(result)


class BareOaiRecord(object):
    source = None # expected to be an OaiSorce
    
    identifier = None
    splash_url = None
    pdf_url = None
    description = None
    keyworks = None
    contributors = None
    pubtype = None
    priority = None

    def update_priority(self):
        self.priority = self.source.priority

    def __unicode__(self):
        """
        The record's identifier
        """
        return self.identifier

    def json(self):
        """
        Dumps the OAI record as a JSON object (for dataset dumping purposes)
        """
        return remove_nones({
                'source':self.source.identifier,
                'identifier':self.identifier,
                'splash_url':self.splash_url,
                'pdf_url':self.pdf_url,
                'abstract':self.description,
                'keywords':self.keywords,
                'contributors':self.contributors,
                'type':self.pubtype,
                })




