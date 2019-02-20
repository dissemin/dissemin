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

import os
import requests_mock

from django.test import TestCase
from publishers.romeo import RomeoAPI
from publishers.models import Journal
from publishers.models import Publisher
from lxml import etree

class RomeoAPIStub(RomeoAPI):
    def __init__(self, datadir):
        super(RomeoAPIStub, self).__init__()
        self.datadir = datadir
        
    def perform_romeo_query(self, search_terms):
        filename = '_'.join(sorted('{}-{}'.format(key, val.replace(' ','_')) for key, val in search_terms.items())) + '.xml'
        try:
            with open(os.path.join(self.datadir, filename), 'rb') as response_file:
                parser = etree.XMLParser(encoding='ISO-8859-1')
                return etree.parse(response_file, parser)
        except IOError:
            xml = super(RomeoAPIStub, self).perform_romeo_query(search_terms)
            with open(os.path.join(self.datadir, filename), 'wb') as response_file:
                xml.write(response_file)
            return xml

# SHERPA/RoMEO interface
class RomeoTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(RomeoTest, cls).setUpClass()
        cls.testdir = os.path.dirname(os.path.abspath(__file__))
        cls.api = RomeoAPIStub(os.path.join(cls.testdir, 'data'))
        
        with open(os.path.join(cls.testdir, 'data/issn-0022-328X.xml'), 'rb') as issn_file:
            cls.issn_response = issn_file.read()
        with open(os.path.join(cls.testdir, 'data/jtitle-Physical_Review_E.xml'), 'rb') as jtitle_file:
            cls.jtitle_response = jtitle_file.read()

    def test_perform_query(self):
        api = RomeoAPI(domain='www.sherpa.ac.uk', api_key=None)
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://www.sherpa.ac.uk/romeo/api29.php?issn=0022-328X',
                content=self.issn_response)
            http_mocker.get('http://www.sherpa.ac.uk/romeo/api29.php?jtitle=Physical%20Review%20E',
                content=self.jtitle_response)
            
            self.assertIsInstance(api.perform_romeo_query(
                {'issn': '0022-328X'}), etree._ElementTree)
            self.assertIsInstance(api.perform_romeo_query(
                {'jtitle': 'Physical Review E'}), etree._ElementTree)

    def test_fetch_journal(self):
        terms = {'issn': '0022-328X'}
        orig_terms = terms.copy()
        self.assertIsInstance(self.api.fetch_journal(terms), Journal)
        self.assertEqual(terms, orig_terms)
        journal = self.api.find_journal_in_model(terms)
        self.assertIsInstance(journal, Journal)
        self.assertEqual(journal.issn, terms['issn'])

    def test_fetch_publisher(self):
        self.assertEqual(self.api.fetch_publisher(None), None)
        self.assertEqual(self.api.fetch_publisher('Harvard University Press').romeo_id, "3243")
        
    def test_fetch_publisher_long_copyrightlink(self):
        publisher = self.api.fetch_publisher('Presses Universitaires de Nancy - Editions Universitaires de Lorraine')
        self.assertEqual(publisher.romeo_id, 'some_id')
        
    def test_fetch_publisher_dump(self):
        self.api.fetch_all_publishers()
        self.assertEqual(Publisher.objects.get(name='1066 Tidsskrift for historie').romeo_id, '1939')

    def test_unicode(self):
        terms = {'issn': '0375-0906'}
        journal = self.api.fetch_journal(terms)
        self.assertEqual(
            journal.title, 'Revista de Gastroenterología de México')
        self.assertEqual(journal.publisher.name, 'Elsevier España')

    def test_ampersand(self):
        terms = {'issn': '0003-1305'}
        journal = self.api.fetch_journal(terms)
        self.assertEqual(journal.publisher.name, 'Taylor & Francis')

    def test_overescaped(self):
        terms = {'issn': '2310-0133'}
        journal = self.api.fetch_journal(terms)
        self.assertEqual(journal.publisher.alias,
                         'Научный издательский дом Исследов')

    def test_too_long(self):
        terms = {'jtitle': ("Volume 3: Industrial Applications; Modeling "
                            "for Oil and Gas, Control and Validation, Estimation, and Control of "
                            "Automotive Systems; "
                            "Design; Physical Human-Robot Interaction; "
                            "Rehabilitation Robotics; Sensing and Actuation for Control; Biomedical "
                            "Systems; Time Delay Systems and Stability; Unmanned Ground and Surface "
                            "Robotics; Vehicle Motion Controls; Vibration Analysis and Isolation; "
                            "Vibration and Control for Energy Harvesting; Wind Energy")}
        self.assertEqual(self.api.fetch_journal(terms), None)

    def test_openaccess(self):
        self.assertEqual(self.api.fetch_journal(
            {'issn': '1471-2105'}).publisher.oa_status, 'OA')
        self.assertEqual(self.api.fetch_journal(
            {'issn': '1951-6169'}).publisher.oa_status, 'OA')

    def test_closed(self):
        self.assertEqual(self.api.fetch_journal(
            {'issn': '0001-4826'}).publisher.oa_status, 'NOK')

    def test_open(self):
        self.assertEqual(self.api.fetch_journal(
            {'issn': '1631-073X'}).publisher.oa_status, 'OK')
        self.assertEqual(self.api.fetch_journal(
            {'issn': '0099-2240'}).publisher.oa_status, 'OK')
        self.assertEqual(self.api.fetch_journal(
            {'issn': '0036-8075'}).publisher.oa_status, 'OK')

