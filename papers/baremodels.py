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

from __future__ import unicode_literals

import re

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from papers.utils import sanitize_html
from papers.utils import datetime_to_date
from papers.utils import iunaccent
from papers.utils import remove_diacritics
from papers.utils import remove_nones
from papers.utils import validate_orcid
from papers.utils import tolerant_datestamp_to_datetime
from papers.categories import PAPER_TYPE_CHOICES
from papers.categories import PAPER_TYPE_PREFERENCE
from papers.oaisource import OaiSource
from publishers.models import DummyPublisher
from publishers.models import Journal
from publishers.models import Publisher
from publishers.models import OA_STATUS_CHOICES
from publishers.models import OA_STATUS_PREFERENCE
MAX_NAME_LENGTH = 256


class BareObject(object):
    """
    A Bare object contains the skeleton for a non-bare (Django model) class.
    Its fields are stored in memory only and it does not correspond to a DB entry.
    To convert a bare object to its non-bare counterpart, for instance a BareName `b`
    into a Name, use `Name.from_bare(b)`.
    """
    _bare_fields = []
    _bare_foreign_key_fields = {}
    _mandatory_fields = []

    def __init__(self, *args, **kwargs):
        """
        Keyword arguments can be used to set fields of this bare object.
        """
        super(BareObject, self).__init__()
        for f in self._bare_fields + self._bare_foreign_key_fields.keys():
            if not hasattr(self, f):
                setattr(self, f, None)
        for f in self._bare_foreign_key_fields:
            if f+'_id' not in self.__dict__:
                setattr(self, f+'_id', None)
                setattr(self, '_%s_cache' % f, None)

        for k, v in kwargs.items():
            self.__setattr__(k, v, restrict_to_fields=True)

    def __setattr__(self, k, v, restrict_to_fields=False):
        if k in self._bare_fields:
            object.__setattr__(self, k, v)
        elif k in self._bare_foreign_key_fields:
            object.__setattr__(self, '_%s_cache' % k, v)
            if v is None:
                object.__setattr__(self, k+'_id', None)
            elif v.id:
                object.__setattr__(self, k+'_id', v.id)
            else:
                raise ValueError(
                    'Assigning an unsaved instance to a ForeignKey')
        elif (k.endswith('_id') and k[:-3] in
                    self._bare_foreign_key_fields):
            cached_instance_key = '_%s_cache' % k[:-3]
            cached_instance = self.__dict__.get(cached_instance_key)
            self.__dict__[k] = v
            if cached_instance and cached_instance.id != v:
                self.__dict__[cached_instance_key] = None
        elif restrict_to_fields:
            raise ValueError('Unexpected keyword argument '+k)
        else:
            self.__dict__[k] = v

    def __getattr__(self, k):
        if k in self._bare_foreign_key_fields:
            cached_value = self.__dict__.get(k)
            if cached_value:
                return cached_value
            else:
                id = self.__dict__.get(k+'_id')
                if id:
                    cls = self._bare_foreign_key_fields[k]
                    return cls.objects.get(id=id)
        else:
            self.__dict__[k]

    def fields_dict(self, foreign_ids=False):
        """
        Returns a dict with the fields' values
        
        :param foreign_ids: if True, stores values of foreign fields
            as ids rather than as model instances.
        """
        dct = {}
        fields = self._bare_fields + self._bare_foreign_key_fields.keys()
        for k, v in self.__dict__.items():
            if (k in self._bare_fields or
                (k.endswith('_id') and
                 k[:-3] in self._bare_foreign_key_fields and
                 foreign_ids) or
                (k in self._bare_foreign_key_fields and
                 not foreign_ids)):
                dct[k] = v
                
        return dct

    @classmethod
    def from_bare(cls, bare_obj):
        """
        This creates an instance of the current class as a copy of a
        bare instance. Concretely, this copies all the fields contained
        in the bare object to an instance of the current class, which
        is expected to be a subclass of the bare object's class.
        """
        kwargs = bare_obj.fields_dict()
        ist = cls(**kwargs)
        return ist

    def breadcrumbs(self):
        """
        Breadcrumbs of bare objects are empty by default.
        """
        return [(unicode(self), '#')]

    def check_mandatory_fields(self):
        """
        Raises `ValueError` if any field is missing.
        The list of mandatory fields for the class should be stored in `_mandatory_fields`.
        """
        for field in self._mandatory_fields:
            if (not getattr(self, field, None) and
                not getattr(self, field+'_id', None)):
                raise ValueError('No %s provided to create a %s.' %
                                 (field, self.__class__.__name__))

class BareAuthor(BareObject):
    """
    The base class for the author of a paper.
    This holds the name of the author, its position in the authors list,
    and its possible affiliations.
    """
    _bare_fields = [
        'affiliation',
        'orcid',
        'researcher_id',
        'name',
    ]
    _mandatory_fields = [
        'name',
    ]

    @cached_property
    def _researcher_model(self):
        return apps.get_app_config('papers').get_model('Researcher')

    @cached_property
    def researcher(self):
        """
        Returns the :class:`Researcher` object associated with
        this author (if any)
        """
        if self.researcher_id:
            return self._researcher_model.objects.get(id=self.researcher_id)

    @property
    def is_known(self):
        """
        An author is "known" when it is linked to a known researcher.
        """
        return self.researcher != None

    def update_name_variants_if_needed(self, default_confidence=0.1):
        """
        Ensure that an author associated with an ORCID has a name
        that is the variant of the researcher with that ORCID
        """
        orcid = self.orcid
        if orcid:
            try:
                r = self._researcher_model.objects.get(orcid=orcid)
                NameVariant = apps.get_app_config(
                    'papers').get_model('NameVariant')
                NameVariant.objects.get_or_create(
                        researcher=r,
                        name=self.name,
                        defaults={'confidence': default_confidence})
            except ObjectDoesNotExist:
                pass

    # Representations -------------------------------
    def __unicode__(self):
        """
        Unicode representation: name of the author
        """
        return unicode(self.name)

    def serialize(self):
        """
        JSON representation for storage in a JSON field
        (internal, not to be used as the output of the API)
        """
        return {
            'name': self.name.serialize(),
            'orcid': self.orcid,
            'affiliation': self.affiliation,
            'researcher_id': self.researcher_id,
            }

    @classmethod
    def deserialize(cls, rep):
        """
        Creates an Author object out of a serialized representation.
        """
        name = BareName.deserialize(rep['name'])
        inst = cls(
            affiliation=rep.get('affiliation'),
            orcid=rep.get('orcid'),
            name=name,
            researcher_id=rep.get('researcher_id'),
            )
        return inst

    def json(self):
        """
        JSON representation of the author for dataset dumping purposes,
        or for the public API.
        """
        orcid_id = self.orcid
        affiliation = None
        if not orcid_id and self.affiliation:
            affiliation = self.affiliation
        return remove_nones({
                'name': self.name.json(),
                'affiliation': affiliation,
                'orcid': orcid_id,
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
        return '%s %s' % (self.first, self.last)

    def first_letter(self):
        """
        First letter of the last name, for sorting purposes
        """
        return self.last[0]

    def serialize(self):
        """
        JSON representation for internal storage purposes
        """
        return {
            'first': self.first,
            'last': self.last,
            'full': self.full,
            }

    @classmethod
    def deserialize(cls, rep):
        """
        Reconstruct an object based on its serialized representation
        """
        inst = cls(
            first=rep['first'],
            last=rep['last'],
            full=rep['full'],
            )
        return inst

    def json(self):
        """
        Returns a JSON representation of the name (for external APIs)
        """
        return {
                'first': self.first,
                'last': self.last,
               }

    def __hash__(self):
        return self.full.__hash__()

    def __eq__(self, other):
        return self.full == other.full



class BareOaiRecord(BareObject):
    _bare_foreign_key_fields = {
        'source': OaiSource,
        'journal': Journal,
        'publisher': Publisher,
    }

    _bare_fields = [
        'identifier',
        'splash_url',
        'pdf_url',
        'description',
        'keywords',
        'contributors',
        'pubtype',
        'priority',
        'journal_title',
        'container',
        'publisher_name',
        'issue',
        'volume',
        'pages',
        'pubdate',
        'doi',
    ]

    _mandatory_fields = [
        'identifier',
        'splash_url',
        'source',
    ]

    def __init__(self, *args, **kwargs):
        super(BareOaiRecord, self).__init__(*args, **kwargs)
        if self.source:
            self.priority = self.source.priority

    def __hash__(self):
        return self.identifier.__hash__()

    def __eq__(self, other):
        return self.identifier == other.identifier

    def update_priority(self):
        self.priority = self.source.priority

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

    def full_journal_title(self):
        """
        The full title of the journal, otherwise the title present
        in CrossRef's metadata, which might be shorter.
        """
        if self.journal:
            return self.journal.title
        else:
            return self.journal_title

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

    def has_publication_metadata(self):
        """
        Does this record tell where the paper is published?
        If so we can use it to look up the policy in RoMEO.
        """
        return bool(self.journal_title and self.publisher_name)

    def source_or_publisher(self):
        """
        Returns the name of the source to display.
        If the record comes from a repository that we index
        directly via OAI-PMH, we return the name of the source.
        If the record has a publisher name, we return the
        publisher name.
        """
        if self.publisher:
            return self.publisher.name
        return self.source.name

    def cleanup_description(self):
        """
        Removes clutter frequently included in abstracts.
        Note that this does not save the object (being
        a method of BareOaiRecord).
        """
        if not self.description:
            return
        abstract_re = re.compile(
            r'^\s*(abstract|international audience)\s*(\.|:|;)\s',
            flags=re.IGNORECASE)
        self.description = abstract_re.sub('', self.description)

    def __unicode__(self):
        """
        The record's identifier
        """
        return self.identifier

    def json(self):
        """
        Dumps the OAI record as a JSON object (to expose it in the API)
        Not to be confused with the serialization method to store
        the record in the database, serialize().
        """
        result = {}
        if self.publisher:
            result['policy'] = self.publisher.json()
        if self.journal:
            result['issn'] = self.journal.issn
        result.update({
                'source': self.source.identifier,
                'identifier': self.identifier,
                'splash_url': self.splash_url,
                'pdf_url': self.pdf_url,
                'doi': self.doi,
                'abstract': self.description,
                'keywords': self.keywords,
                'contributors': self.contributors,
                'type': self.pubtype,
                'publisher': self.publisher_name,
                'journal': self.full_journal_title(),
                'container': self.container,
                'issue': self.issue,
                'volume': self.volume,
                'pages': self.pages,
                })
        return remove_nones(result)

    def serialize(self):
        """
        Serializes the record for JSON storage in a Paper object.
        """
        fields = self.fields_dict(foreign_ids=True)
        if fields.get('pubdate'):
            fields['pubdate'] = fields['pubdate'].isoformat()
        return fields 
    
    @classmethod
    def deserialize(cls, dct):
        """
        Returns a BareOaiRecord from the serialized JSON value
        """
        newdct = dct.copy()
        if dct.get('pubdate'):
            newdct['pubdate'] = datetime_to_date(
                        tolerant_datestamp_to_datetime(dct['pubdate']))
        return cls(**newdct)

    def __repr__(self):
        return "<BareOaiRecord %s>" % unicode(self.identifier)
