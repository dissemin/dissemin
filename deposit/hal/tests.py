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

from deposit.hal.metadata import AOFRFormatter
from deposit.hal.protocol import HALProtocol
from deposit.tests import ProtocolTest
from django.test import TestCase
from papers.models import Paper
from unittest import expectedFailure
from backend.oai import OaiPaperSource
from backend.oai import BASEDCTranslator

from backend.oai import get_proaixy_instance

#from os import path


class AOFRTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(AOFRTest, cls).setUpClass()

        # This currently fails and is unused

        #xsd_fname = path.join(path.dirname(__file__), 'aofr-sword.xsd')
        # with open(xsd_fname, 'r') as f:
        #   elem = etree.parse(f)
        #   cls.xsd = etree.XMLSchema(elem)

    def test_generate_metadata_doi(self):
        # f =
        AOFRFormatter()
        dois = ['10.1175/jas-d-15-0240.1']
        for doi in dois:
            Paper.create_by_doi(doi)
            #form = TODO
            #rendered = f.render(p, 'article.pdf', form)
            # with open('/tmp/xml_validation.xml', 'w') as f:
            #    f.write(etree.tostring(rendered, pretty_print=True))
            # XSD validation currently fails
            # self.xsd.assertValid(rendered)


class HALProtocolTest(ProtocolTest):

    @classmethod
    def setUpClass(self):
        super(HALProtocolTest, self).setUpClass()
        self.repo.username = 'test_ws'
        self.repo.password = 'test'
        # f =
        self.proto = HALProtocol(self.repo)

    @expectedFailure
    def test_lncs_many_authors(self):
        """
        Submit a paper from LNCS (type: book-chapter).
        This fails with the default test account because
        it does not have the right to deposit with only one
        affiliation.
        """
        p = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        r = self.dry_deposit(p,
            abstract='this is an abstract',
            topic='INFO',
            depositing_author=0,
            affiliation=59704) # ENS
        self.assertEqual(r.status, 'faked')

    def test_lncs(self):
        """
        Same as test_lncs but with only one author
        """
        p = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
        p.authors_list = [p.authors_list[0]]
        r = self.dry_deposit(p,
            abstract='this is an abstract',
            topic='INFO',
            depositing_author=0,
            affiliation=59704) # ENS
        self.assertEqual(r.status, 'faked')


    def test_lics(self):
        """
        Submit a paper from LICS (type: conference-proceedings)
        """
        p = Paper.create_by_doi('10.1109/lics.2015.37')
        p.authors_list = [p.authors_list[0]]
        r = self.dry_deposit(p,
             abstract='here is my great result',
             topic='NLIN',
             depositing_author=0,
             affiliation=128940)
        self.assertEqual(r.status, 'faked')

    def test_journal_article(self):
        """
        Submit a journal article
        """
        p = Paper.create_by_doi('10.1016/j.agee.2004.10.001')
        p.authors_list = [p.authors_list[0]]
        r = self.dry_deposit(p,
             abstract='here is my great result',
             topic='SDV',
             depositing_author=0,
             affiliation=128940)
        self.assertEqual(r.status, 'faked')

    def test_preprint(self):
        """
        Submit a preprint
        """
        oai = OaiPaperSource(endpoint='http://doai.io/oai')
        oai.add_translator(BASEDCTranslator())
        p = oai.create_paper_by_identifier('ftarxivpreprints:oai:arXiv.org:1207.2079', 'base_dc')
        p.authors_list = [p.authors_list[0]]
        r = self.dry_deposit(p,
             abstract='here is my great result',
             topic='SDV',
             depositing_author=0,
             affiliation=128940)
        self.assertEqual(r.status, 'faked')

    def test_paper_already_in_hal(self):
        p = get_proaixy_instance().create_paper_by_identifier(
            'ftunivsavoie:oai:HAL:hal-01062241v1', 'base_dc')
        enabled = self.proto.init_deposit(p, self.user)
        self.assertFalse(enabled)

    def test_predict_topic(self):
        cases = [
                ('IBEX: Harvesting Entities from the Web Using Unique Identifiers', 'INFO'),
                ('Global climate change entails many threats and challenges for the majority of crops.', 'SDV'),
                ('', None),
            ]
        for text, topic in cases:
            self.assertEqual(self.proto.predict_topic(text), topic)
