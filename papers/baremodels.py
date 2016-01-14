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
from papers.name import to_plain_name
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

class BareObject(object):
    """
    A Bare object contains the skeleton for a non-bare (Django model) class.
    Its fields are stored in memory only and it does not correspond to a DB entry.
    To convert a bare object to its non-bare counterpart, for instance a BareName `b`
    into a Name, use `Name.from_bare(b)`.
    """
    _bare_fields = []
    _bare_foreign_key_fields = []
    _mandatory_fields = []

    def __init__(self, *args, **kwargs):
        """
        Keyword arguments can be used to set fields of this bare object.
        """
        super(BareObject, self).__init__()
        for f in self._bare_fields + self._bare_foreign_key_fields:
            if not hasattr(self, f):
                self.__dict__[f] = None
        for f in self._bare_foreign_key_fields:
            if f+'_id' not in self.__dict__:
                self.__dict__[f+'_id'] = None
        for k, v in kwargs.items():
            if k in self._bare_fields:
                self.__dict__[k] = v
            elif k in self._bare_foreign_key_fields:
                self.__dict__[k] = v
                if hasattr(v, 'id'):
                    self.__dict__[k+'_id'] = v.id
                else:
                    self.__dict__[k+'_id'] = None

    @classmethod
    def from_bare(cls, bare_obj):
        """
        This creates an instance of the current class as a copy of a
        bare instance. Concretely, this copies all the fields contained
        in the bare object to an instance of the current class, which
        is expected to be a subclass of the bare object's class.
        """
        kwargs = {}
        for k, v in bare_obj.__dict__.items():
            if k in cls._bare_fields:
                kwargs[k] = v
            elif k in cls._bare_foreign_key_fields:
                kwargs[k] = v

        ist = cls(**kwargs)
        return ist

    def breadcrumbs(self):
        """
        Breadcrumbs of bare objects are empty by default.
        """
        return [(unicode(self),'#')]

    def check_mandatory_fields(self):
        """
        Raises `ValueError` if any field is missing.
        The list of mandatory fields for the class should be stored in `_mandatory_fields`.
        """
        for field in self._mandatory_fields:
            if not self.__dict__.get(field):
                raise ValueError('No %s provided to create a %s.' %
                        (field,self.__class__.__name__))

class BarePaper(BareObject):
    """
    This class is the bare analogue to :class:`Paper`. Its authors are
    lists of :class:`BareName`, and its publications and OAI records are also bare.
    """
    _bare_fields = [
        #! The title of the paper
        'title',
        #! The fingerprint (robust version of the title, authors and year)
        'fingerprint',
        #! The publication date
        'pubdate',
        #! The document type
        'doctype',
        #! The OA status
        'oa_status',
        #! The url where we think the full text is available
        'pdf_url',
        #! Visibility
        'visibility',
    ]

    _mandatory_fields = [
        'title',
        'pubdate',
        'fingerprint',
    ]

    ### Creation

    def __init__(self, *args, **kwargs):
        super(BarePaper, self).__init__(*args, **kwargs)
        #! The authors: a list of :class:`BareName`
        self.bare_authors = []
        #! The publications associated with this paper: a list of :class:`BarePublication` indexed by their dois
        self.bare_publications = {}
        #! The OAI records associated with this paper: dict of :class:`BareOaiRecord` indexed by their identifiers
        self.bare_oairecords = {}
        #! If there are lots of authors, how many are we hiding?
        self.nb_remaining_authors = None

    @classmethod
    def from_bare(cls, bare_obj):
        """
        Creates an instance of this class from a :class:`BarePaper`.
        """
        ist = super(BarePaper, cls).from_bare(bare_obj)
        ist.save()
        for p in bare_obj.publications:
            ist.add_publication(p)
        for r in bare_obj.oairecords:
            ist.add_oairecord(r)
        for idx, a in enumerate(bare_obj.authors):
            ist.add_author(a, position=idx)
        ist.fingerprint = ist.new_fingerprint()
        ist.update_availability()
        ist.update_visibility()
        return ist


    @classmethod
    def create(cls, title, author_names, pubdate, visibility='VISIBLE', affiliations=None):
        """
        Creates a (bare) paper. To save it to the database, we
        need to run the clustering algorithm to resolve Researchers for the authors,
        using `from_bare` from the (non-bare) :class:`Paper` subclass..

        :param title: The title of the paper (as a string). If it is too long for the database,
                      ValueError is raised.
        :param author_names: The ordered list of author names, as Name objects.
        :param pubdate: The publication date, as a python date object
        :param visibility: The visibility of the paper if it is created. If another paper
                    exists, the visibility will be set to the maximum of the two possible
                    visibilities.
        :param affiliations: A list of (possibly None) affiliations for the authors. It has to 
                    have the same length as the list of author names. Affiliations can be replaced by ORCIDs.
        """
        plain_names = map(to_plain_name, author_names)
        
        if not title or not author_names or not pubdate:
            raise ValueError("A title, pubdate and authors have to be provided to create a paper.")

        if affiliations is not None and len(author_names) != len(affiliations):
            raise ValueError("The number of affiliations and authors have to be equal.")
        if visibility not in [c for (c,_) in VISIBILITY_CHOICES]:
            raise ValueError("Invalid paper visibility: %s" % unicode(visibility))

        title = sanitize_html(title)
        title = maybe_recapitalize_title(title)

        p = cls()
        p.title = title
        p.pubdate = pubdate
        p.visibility = visibility
        for idx, n in enumerate(author_names):
            a = BareAuthor()
            a.name = n
            if affiliations is not None:
                a.affiliation = affiliations[idx]
            p.add_author(a, position=idx)

        p.fingerprint = p.new_fingerprint()

        return p


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
        return self.bare_publications.values()

    @property
    def oairecords(self):
        """
        The list of OAI records associated with this paper. It can
        be arbitrary iterables of subclasses of :class:`BareOaiRecord`.
        """
        return self.bare_oairecords.values()

    def add_author(self, author, position=None):
        """
        Adds a new author to the paper, at the end of the list.

        :param position: if provided, set the author to the given position.

        :returns: the :class:`BareAuthor` that was added (it can differ in subclasses)
        """
        self.bare_authors.append(author)
        return author

    def add_oairecord(self, oairecord):
        """
        Adds a new OAI record to the paper

        :returns: the :class:`BareOaiRecord` that was added (it can differ in subclasses)
        """
        oairecord.check_mandatory_fields()
        self.bare_oairecords[oairecord.identifier] = oairecord
        return oairecord

    def add_publication(self, publication):
        """
        Adds a new publication to the paper

        :returns: the :class:`BarePublication` that was added (it can differ in subclasses)
        """
        publication.check_mandatory_fields()
        self.bare_publications[publication.doi] = publication
        return publication

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

    def affiliations(self):
        """
        The list of affiliations of all authors
        """
        return [a.affiliation for a in self.authors]

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

    def check_authors(self):
        """
        Check that all authors are associated with a valid name.
        (This is normally enforced by the database but in some contexts
        where names are cached, this was not the case.)
        """
        for a in self.authors:
            if a.name is None:
                raise ValueError("Name referenced by author could not be found!")

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
        # TODO this should be moved to the non-bare Paper I think
        # so that we can remove the ugly hasattr
        p = self
        if p.visibility != 'VISIBLE' and p.visibility != 'NOT_RELEVANT':
            return
        researcher_found = False
        for a in p.authors:
            if hasattr(a, 'researcher_id') and a.researcher_id:
                researcher_found = True
                break
        if researcher_found and p.visibility != 'VISIBLE':
            p.visibility = 'VISIBLE'
            if hasattr(self, 'pk'):
                p.save(update_fields=['visibility'])
        elif not researcher_found and p.visibility != 'NOT_RELEVANT':
            p.visibility = 'NOT_RELEVANT'
            if hasattr(self, 'pk'):
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

class BareAuthor(BareObject):
    """
    The base class for the author of a paper.
    This holds the name of the author, its position in the authors list,
    and its possible affiliations.
    """
    _bare_fields = [
        'affiliation',
    ]
    _bare_foreign_key_fields = [
        'name',
    ]
    _mandatory_fields = [
        'name',
    ]

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


class BareName(BareObject):
    _bare_fields = [
        'first',
        'last',
        'full',
    ]

    _mandatory_fields = [
        'last',
        # first name can be empty, full is generated from first and last
    ]

    @classmethod
    def create_bare(cls, first, last):
        """
        Same as `create`, provided for uniformity among bare classes.
        """
        return cls.create(first, last)

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


class BarePublication(BareObject):
    _bare_fields = [
        'pubtype',
        'title', # this is actually the *journal* title
        'container',
        'publisher_name',
        'issue',
        'volume',
        'pages',
        'pubdate',
        'abstract',
        'doi',
        'pdf_url',
        ]

    _bare_foreign_key_fields = [
        'journal', # expected to be an actual model instance
        'publisher', # expected to be an actual model instance
    ]
    
    _mandatory_fields = [
        'pubtype',
        'title',
    ]

    def oa_status(self):
        """
        Policy of the publisher for this publication
        """
        if self.pdf_url:
            return 'OA'
        elif self.publisher:
            if self.publisher.oa_status == 'OA' and self.doi:
                self.pdf_url = 'http://dx.doi.org/'+self.doi
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


class BareOaiRecord(BareObject):
    _bare_foreign_key_fields = [
        'source', # expected to be an OaiSorce
    ]
    
    _bare_fields = [
        'identifier',
        'splash_url',
        'pdf_url',
        'description',
        'keywords',
        'contributors',
        'pubtype',
        'priority',
    ]

    _mandatory_fields = [
        'identifier',
        'splash_url',
        'source',
    ]

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




