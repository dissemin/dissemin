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

from __future__ import unicode_literals

import unittest
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from backend.oai import OaiPaperSource
from backend.oai import BASEDCTranslator
from backend.oai import OAIDCTranslator
from backend.oai import CiteprocTranslator
from papers.models import OaiRecord
from papers.baremodels import BareOaiRecord
from oaipmh.error import BadArgumentError
from papers.errors import *

class OaiTest(TestCase):
    def setUp(self):
        self.oai = OaiPaperSource(endpoint='http://doai.io/oai')
        self.oai.add_translator(BASEDCTranslator())
        self.oai.add_translator(OAIDCTranslator())
        self.oai.add_translator(CiteprocTranslator())

    def create(self, *args, **kwargs):
        # Shortcut for the tests
        return self.oai.create_paper_by_identifier(*args, **kwargs)

    def delete(self, identifier):
        try:
            r = OaiRecord.objects.get(identifier=identifier)
            p = r.about
            r.delete()
            if p.is_orphan():
                p.delete()
        except OaiRecord.DoesNotExist:
            pass

    def test_create_no_match(self):
        """
        Creation of a paper from an OAI record,
        when the paper does not exist yet.
        """
        pass
    
    def test_create_already_existing(self):
        """
        Creation of a paper from an OAI record,
        when the exact same OAI record already exists.
        """
        pass
    
    def test_create_match_fp(self):
        """
        Addition of an OAI record when it is matched
        with an existing record by fingerprint.
        """
        pass

    def test_create_match_doi(self):
        """
        Addition of an OAI record when it is matched
        to an existing paper by DOI
        """
        # first, make sure the paper isn't there already
        self.delete('oai:crossref.org:10.1007/s10858-015-9994-8')
        # Create a paper from BASE
        spoc = self.create(
            'ftspringeroc:10.1007/s10858-015-9994-8',
            'base_dc')

        records_before = set(spoc.oairecords)
        new_paper = self.create(
            'oai:crossref.org:10.1007/s10858-015-9994-8',
            'citeproc')
        self.assertEqual(self.spoc, new_paper)
        records_before.add(OaiRecord.objects.get(identifier=
            'oai:crossref.org:10.1007/s10858-015-9994-8'))
        self.assertEqual(set(new_paper.oairecords), records_before)

    def test_create_match_identifier(self):
        """
        An OAI record with the same identifier already
        exists but it has been already merged before with
        another paper with a different fingerprint.
        """
        pass

    def test_create_invalid_metadata(self):
        """
        Metadata that we don't accept
        """
        identifiers = [
        # Contributors too long to fit in the db
        ('ftbnfgallica:oai:bnf.fr:gallica/ark:/12148/btv1b8621766k',
        'base_dc'),
        # No authors
        ('ftcarmelhelios:oai:archive.library.cmu.edu:heinz:box00200/fld00021/bdl0031/doc0001/',
        'base_dc'),
         ]
        for i, f in identifiers:
            self.assertEqual(
                self.create(i, f),
                None)

    def test_create_invalid_identifier(self):
        """
        Fetching an invalid identifier from OAI
        """
        with self.assertRaises(BadArgumentError):
            self.create('aiunrsecauiebleuiest', 'oai_dc')
    
    def test_create_invalid_format(self):
        """
        Fetching with an invalid format from OAI
        """
        # Format not registered
        # TODO
        # Format not available from the interface
        with self.assertRaises(BadArgumentError):
            self.create('aiunrsecauiebleuiest', 'unknown_format')
        


