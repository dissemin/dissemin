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



import os
import re
import unittest
import requests_mock
import pytest
from mock import patch
from oaipmh.client import Client

from deposit.models import License
from deposit.models import LicenseChooser
from deposit.tests import lorem_ipsum
from deposit.tests.test_protocol import ProtocolTest
from deposit.zenodo.protocol import ZenodoProtocol
from deposit.models import Repository
from papers.models import Paper
from papers.models import OaiSource

class ZenodoProtocolTest(ProtocolTest):

    def setUp(self):
        super(ZenodoProtocolTest, self).setUp()
        if 'ZENODO_SANDBOX_API_KEY' not in os.environ:
            raise unittest.SkipTest(
                "Environment variable ZENODO_SANDBOX_API_KEY is undefined")
        self.setUpForProtocol(ZenodoProtocol, Repository(
            name='Zenodo Sandbox',
            endpoint='https://sandbox.zenodo.org/api/deposit/depositions',
            api_key=os.environ['ZENODO_SANDBOX_API_KEY'],
        ))

        self.testdir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.testdir, 'testdata/zenodo_record.xml'), 'r') as f:
            self.zenodo_record = f.read()

        self.l = License.objects.get(uri="https://dissem.in/deposit/license/zenodo-freetoread-1.0/")
        self.lc, unused = LicenseChooser.objects.get_or_create(
            license=self.l,
            repository=self.repo,
            transmit_id='zenodo-freetoread-1.0',
            default=True,
        )

    @pytest.mark.usefixtures('mock_doi')
    def test_lncs(self):
        p = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')

        r = self.dry_deposit(p,
            abstract = lorem_ipsum,
            license = self.lc)
        self.assertEqualOrLog(r.status, 'faked')

    @patch.object(Client, 'makeRequest')
    def test_try_deposit_paper_already_on_zenodo(self, mock_makeRequest):
        """
        If the paper is already known to be on Zenodo by Dissemin,
        ``init_deposit`` should return ``False`` to prevent any new deposit.
        """
        oaisource = OaiSource.objects.get(identifier='zenodo')
        oaisource.endpoint = 'http://example.com/' # not actually used as we are mocking the HTTP call
        oaisource.save()

        mock_makeRequest.return_value = self.zenodo_record

        p = Paper.create_by_oai_id('oai:pubmedcentral.nih.gov:4131942', source=oaisource)
        enabled = self.proto.init_deposit(p, self.user)
        self.assertFalse(enabled)

    @unittest.skip("""
    It seems that Zenodo have changed their logic here.
    Now, depositing a paper with a DOI that is already in Zenodo
    will result in the new deposition being still created,
    but with the DOI ignored (so, a Zenodo DOI assigned).
    """)
    def test_paper_already_on_zenodo(self):
        """
        In this case, Dissemin missed the paper on Zenodo
        (for some reason) and so the deposit interface was
        enabled. But Zenodo refuses the deposit! We have to
        give a good error message to the user.
        """
        p = Paper.create_by_doi('10.5281/zenodo.50134')
        r = self.deposit(
            p,
            abstract = lorem_ipsum,
            license = self.lc,
        )

        # Deposit fails: a duplicate is found
        self.assertEqualOrLog(r.status, 'failed')

        # The error message should be specific
        self.assertTrue('already in Zenodo' in r.message)

    def test_500_error(self):
        with requests_mock.Mocker(real_http=True) as mocker:
            mocker.get(re.compile(r'.*\.zenodo\.org/.*'), status_code=500)
            p = Paper.create_by_doi('10.1007/978-3-662-47666-6_5')
            r = self.dry_deposit(p,
                    abstract = lorem_ipsum,
                    license = self.lc)
            self.assertEqual(r.status, 'failed')


