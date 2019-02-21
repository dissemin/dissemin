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

import dateutil.parser
import os
import requests_mock

from django.test import TestCase
from publishers.romeo import RomeoAPI
from publishers.models import Journal
from publishers.models import Publisher
from lxml import etree

class RomeoAPIStub(RomeoAPI):
    def __init__(self):
        super(RomeoAPIStub, self).__init__(api_key='api_key', domain='www.sherpa.ac.uk')
        testdir = os.path.dirname(os.path.abspath(__file__))
        self.datadir = os.path.join(testdir, 'data')
        
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
        cls.api = RomeoAPIStub()
        
        with open(os.path.join(cls.testdir, 'data/issn-0022-328X.xml'), 'rb') as issn_file:
            cls.issn_response = issn_file.read()
        with open(os.path.join(cls.testdir, 'data/jtitle-Physical_Review_E.xml'), 'rb') as jtitle_file:
            cls.jtitle_response = jtitle_file.read()
        with open(os.path.join(cls.testdir, 'data/sample_journals.tsv'), 'rb') as journals_dump_file:
            cls.journals_dump_response = journals_dump_file.read()
        with open(os.path.join(cls.testdir, 'data/latest_update.xml'), 'rb') as latest_update_file:
            cls.latest_update_response = latest_update_file.read()

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
        journal = self.api.fetch_journal(terms)
        self.assertIsInstance(journal, Journal)
        self.assertEqual(journal.issn, terms['issn'])
        self.assertEqual(journal.publisher.last_updated, dateutil.parser.parse('2015-05-01T09:50:58Z'))
        self.assertEqual(terms, orig_terms)
        
        from_model = Journal.find(issn=terms['issn'])
        self.assertEqual(from_model, journal)
        
    def test_fetch_journal_updates_publisher(self):
        # First we have an old version of a publisher record
        p = Publisher(name='Harvard University Press', romeo_id='3243',
                      preprint='can', postprint='can', pdfversion='can', last_updated=None)
        p.classify_oa_status()
        p.save()
        
        # Then we fetch one of its journals
        journal = self.api.fetch_journal({'issn':'0073-0688'})
        
        # That updates the publisher object
        publisher = Publisher.objects.get(id=journal.publisher.id)
        self.assertEqual(publisher.id, p.id)
        self.assertEqual(publisher.preprint, 'unclear')
        self.assertEqual(publisher.last_updated, dateutil.parser.parse('2018-05-10T10:48:27Z'))

    def test_fetch_publisher(self):
        self.assertEqual(self.api.fetch_publisher(None), None)
        
        harvard = self.api.fetch_publisher('Harvard University Press')
        self.assertEqual(harvard.romeo_id, "3243")
        self.assertEqual(harvard.last_updated, dateutil.parser.parse('2018-05-10T10:48:27Z'))
        
        journal = self.api.fetch_journal({'issn':'0073-0688'})
        self.assertEqual(journal.publisher, harvard)
        
    def test_fetch_publisher_long_copyrightlink(self):
        publisher = self.api.fetch_publisher('Presses Universitaires de Nancy - Editions Universitaires de Lorraine')
        self.assertEqual(publisher.romeo_id, '2047')
        
    def test_fetch_dumps(self):
        self.api.fetch_all_publishers()
        self.assertEqual(Publisher.objects.get(alias='Greek National Center of Social Research').romeo_id, '2201')
        
        # mocked separately as a different endpoint is used
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://www.sherpa.ac.uk/downloads/journal-title-issns.php?ak=api_key&format=tsv',
                content=self.journals_dump_response)
            self.api.fetch_all_journals()
            
        j = Journal.objects.get(issn='0013-9696')
        self.assertEqual(j.title, 'Greek Review of Social Research')
        self.assertEqual(j.publisher.romeo_id, '2201')
        
    def test_fetch_updates(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://www.sherpa.ac.uk/downloads/journal-title-issns.php?ak=api_key&format=tsv',
                content=self.journals_dump_response)
            http_mocker.get('http://www.sherpa.ac.uk/downloads/download-dates.php?format=xml',
                content=self.latest_update_response)

            # Fetch all publishers initially
            self.api.fetch_updates()
            p = Publisher.objects.get(alias='GSA Today')
            self.assertEqual(p.last_updated, dateutil.parser.parse('2019-02-14T14:05:19Z'))
            p = Publisher.objects.get(romeo_id='2425')
            self.assertEqual(p.url, 'http://intranet.cvut.cz/')
            
            # Fetch updates again
            self.api.fetch_updates()
            
            # A publisher was updated
            p = Publisher.objects.get(romeo_id='2425')
            self.assertEqual(p.url, 'https://intranet.cvut.cz/')
        
    def test_subsequent_publisher_update(self):
        # Fetch a publisher once
        self.api.fetch_all_publishers(modified_since=dateutil.parser.parse('2016-01-01'))
        p = Publisher.objects.get(alias='Czech Technical University in Prague')
        self.assertEqual(p.last_updated, dateutil.parser.parse('2015-07-22T09:06:34Z'))
        self.assertEqual(p.pdfversion, 'can')
        self.assertTrue('Publisher last reviewed on 22/07/2015' in map(str, p.conditions))
        
        # Refetch it later with updated metadata
        self.api.fetch_all_publishers(modified_since=dateutil.parser.parse('2017-01-01'))
        p = Publisher.objects.get(alias='Czech Technical University in Prague')
        self.assertEqual(p.last_updated, dateutil.parser.parse('2016-08-29T15:22:01Z'))
        self.assertEqual(p.pdfversion, 'cannot')
        self.assertTrue('Publisher last reviewed on 29/08/2016' in map(str, p.conditions))
        self.assertFalse('Publisher last reviewed on 22/07/2015' in map(str, p.conditions))      

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
        
    def test_get_romeo_latest_update_date(self):
        with requests_mock.mock() as http_mocker:
            http_mocker.get('http://www.sherpa.ac.uk/downloads/download-dates.php?ak=api_key&format=xml',
                content=self.latest_update_response)
            
            latest_updates = self.api.get_romeo_latest_update_date()
            
            self.assertEqual(latest_updates, {
                'journals': dateutil.parser.parse('2019-02-20T09:18:52Z'),
                'publishers': dateutil.parser.parse('2019-02-15T10:57:11Z'),
                })
