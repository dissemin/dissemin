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
from django.test import TestCase
from unittest import expectedFailure
from papers.models import Paper
from deposit.tests import ProtocolTest
from deposit.hal.protocol import HALProtocol
from deposit.hal.metadataFormatter import AOFRFormatter
from lxml import etree
from os import path

class AOFRTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(AOFRTest, cls).setUpClass()
        xsd_fname = path.join(path.dirname(__file__), 'aofr-sword.xsd')
        with open(xsd_fname, 'r') as f:
            elem = etree.parse(f)
            cls.xsd = etree.XMLSchema(elem)

    @expectedFailure
    def test_generate_metadata_doi(self):
        f = AOFRFormatter()
        dois = ['10.1175/jas-d-15-0240.1']
        for doi in dois:
            p = Paper.create_by_doi(doi)
            rendered = f.render(p, 'article.pdf')
            with open('/tmp/xml_validation.xml', 'w') as f:
                f.write(etree.tostring(rendered, pretty_print=True))
            self.xsd.assertValid(rendered)

class HALProtocolTest(ProtocolTest):
    @classmethod
    def setUpClass(self):
        super(HALProtocolTest, self).setUpClass()
        self.proto = HALProtocol(self.repo)


