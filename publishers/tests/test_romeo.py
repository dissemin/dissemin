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

from django.test import TestCase
from publishers.romeo import fetch_journal
from publishers.romeo import fetch_publisher
from publishers.romeo import find_journal_in_model
from publishers.romeo import perform_romeo_query
from publishers.models import Journal
from lxml import etree

# SHERPA/RoMEO interface
class RomeoTest(TestCase):

    def test_perform_query(self):
        self.assertIsInstance(perform_romeo_query(
            {'issn': '0022-328X'}), etree._ElementTree)
        self.assertIsInstance(perform_romeo_query(
            {'jtitle': 'Physical Review E'}), etree._ElementTree)

    def test_fetch_journal(self):
        terms = {'issn': '0022-328X'}
        orig_terms = terms.copy()
        self.assertIsInstance(fetch_journal(terms), Journal)
        self.assertEqual(terms, orig_terms)
        journal = find_journal_in_model(terms)
        self.assertIsInstance(journal, Journal)
        self.assertEqual(journal.issn, terms['issn'])

    def test_fetch_publisher(self):
        self.assertEqual(fetch_publisher(None), None)
        # TODO: more tests!

    def test_unicode(self):
        terms = {'issn': '0375-0906'}
        journal = fetch_journal(terms)
        self.assertEqual(
            journal.title, 'Revista de Gastroenterología de México')
        self.assertEqual(journal.publisher.name, 'Elsevier España')

    def test_ampersand(self):
        terms = {'issn': '0003-1305'}
        journal = fetch_journal(terms)
        self.assertEqual(journal.publisher.name, 'Taylor & Francis')

    def test_overescaped(self):
        terms = {'issn': '2310-0133'}
        journal = fetch_journal(terms)
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
        self.assertEqual(fetch_journal(terms), None)

    def test_openaccess(self):
        self.assertEqual(fetch_journal(
            {'issn': '1471-2105'}).publisher.oa_status, 'OA')
        self.assertEqual(fetch_journal(
            {'issn': '1951-6169'}).publisher.oa_status, 'OA')

    def test_closed(self):
        self.assertEqual(fetch_journal(
            {'issn': '0001-4826'}).publisher.oa_status, 'NOK')

    def test_open(self):
        self.assertEqual(fetch_journal(
            {'issn': '1631-073X'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal(
            {'issn': '0099-2240'}).publisher.oa_status, 'OK')
        self.assertEqual(fetch_journal(
            {'issn': '0036-8075'}).publisher.oa_status, 'OK')

