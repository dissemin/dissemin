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
        oai_id ='ftccsdartic:oai:hal.archives-ouvertes.fr:hal-00830421'

        # first, make sure the paper isn't there already
        self.delete(oai_id)
        # create a paper from BASE
        hal_paper = self.create(oai_id, 'base_dc')
        self.assertEqual(len(hal_paper.oairecords), 1)
    
    def test_create_already_existing(self):
        """
        Creation of a paper from an OAI record,
        when the exact same OAI record already exists.
        """
        # TODO we could repeat this for various papers
        oai_id ='ftccsdartic:oai:hal.archives-ouvertes.fr:hal-00830421'

        # first, make sure the paper isn't there already
        self.delete(oai_id)
        # create a paper from BASE
        hal_paper = self.create(oai_id, 'base_dc')
        
        # Create it again!
        new_paper = self.create(oai_id, 'base_dc')

        # It's the same thing!
        self.assertEqual(new_paper, hal_paper)
        self.assertSetEqual(set(new_paper.oairecords), set(hal_paper.oairecords))
        self.assertListEqual(new_paper.bare_author_names(),
                            hal_paper.bare_author_names())
        self.assertEqual(new_paper.title, hal_paper.title)
 
    
    def test_create_match_fp(self):
        """
        Addition of an OAI record when it is matched
        with an existing record by fingerprint.
        """
        # first, make sure the paper isn't there already
        self.delete('ftccsdartic:oai:hal.archives-ouvertes.fr:hal-00939473')
        # create a paper from BASE
        hal_paper = self.create(
            'ftccsdartic:oai:hal.archives-ouvertes.fr:hal-00939473',
            'base_dc')
        
        # Save the existing records
        records = set(hal_paper.oairecords)
        # Create a new paper (refers to the same paper, but coming from
        # another source)
        new_paper = self.create('ftciteseerx:oai:CiteSeerX.psu:10.1.1.487.869',
            'base_dc')
        # the resulting paper has to be equal to the first one
        # (this does not check that all their attributes are equal, just
        # that they are the same row in the database, i.e. have same id)
        self.assertEqual(new_paper, hal_paper)
        # the new set of records is the old one plus the new record
        records.add(OaiRecord.objects.get(identifier=
                'ftciteseerx:oai:CiteSeerX.psu:10.1.1.487.869'))
        self.assertSetEqual(set(new_paper.oairecords), records)

    def test_create_match_doi(self):
        """
        Addition of an OAI record when it is matched
        to an existing paper by DOI
        """
        first_id='ftunivmacedonia:oai:dspace.lib.uom.gr:2159/6240'
        second_id='oai:crossref.org:10.1111/j.1574-0862.2005.00325.x'

        # first, make sure the paper isn't there already
        self.delete(first_id)
        # Create a paper from BASE
        first = self.create(first_id,'base_dc')

        self.assertEqual(first.oairecords[0].doi,
                '10.1111/j.1574-0862.2005.00325.x')
        records = set(first.oairecords)
        new_paper = self.create(second_id, 'citeproc')

        # Make sure that, if a merge happens, the oldest
        # paper remains (otherwise we create broken links!)
        self.assertEqual(first, new_paper)

        records.add(OaiRecord.objects.get(identifier=second_id))
        self.assertEqual(set(new_paper.oairecords), records)

    def test_update_pdf_url(self):
        """
        Two OAI records share the same splash URL, but
        the second one has a pdf_url. We should add the PDF
        url to the existing OAI record (merge the two records).
        """
        # first, make sure the paper isn't there already
        self.delete('oai:crossref.org:10.1007/s10858-015-9994-8')
        # Create a paper from Crossref
        first = self.create(
            'oai:crossref.org:10.1007/s10858-015-9994-8',
            'citeproc')
        # initially the PDF url should be empty 
        self.assertEqual(first.oairecords[0].pdf_url, None)

        # then we import a new identifier
        new_paper = self.create(
            'ftspringeroc:10.1007/s10858-015-9994-8',
            'base_dc')
        self.assertEqual(first, new_paper)

        # no new record should be created
        self.assertEqual(len(new_paper.oairecords), 1)
        self.assertNotEqual(new_paper.oairecords[0].pdf_url, None)


    def test_create_match_identifier(self):
        """
        An OAI record with the same identifier already
        exists but it has been already merged before with
        another paper with a different fingerprint.
        """
        identifier = 'ftccsdartic:oai:hal.archives-ouvertes.fr:hal-00939473'

        # create a paper from BASE
        hal_paper = self.create(identifier, 'base_dc')
        records = set(hal_paper.oairecords)
        # change its fingerprint
        hal_paper.title += ' babebibobu'
        hal_paper.fingerprint = hal_paper.new_fingerprint()
        hal_paper.save()
        
        # add the OAI record again
        new_paper = self.create(identifier, 'base_dc')
        self.assertEqual(new_paper, hal_paper)
        self.assertSetEqual(records, set(new_paper.oairecords))

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
        


