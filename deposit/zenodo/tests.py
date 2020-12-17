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

import json
import os
import pytest
import responses

from django.conf import settings

from deposit.protocol import DepositError
from deposit.tests.test_protocol import MetaTestProtocol
from papers.models import Paper


@pytest.fixture
def metadata():
    """
    Simple snippet of metadata taken from Zenodo API documentation
    """
    data = {
        'metadata': {
            'title': 'My first upload',
            'upload_type': 'poster',
            'description': 'This is my first upload',
            'creators': [{'name': 'Doe, John',
                          'affiliation': 'Zenodo'}]
        }
    }
    return data

@pytest.fixture
def publish_response():
    """
    Simple response from zenodo after successful publish
    """
    data = {
        'conceptrecid': '4308143',
        'created': '2020-12-06T01:52:12.585197+00:00',
        'doi': '10.32463/rphs.2018.v04i02.11',
        'files': [
            {
                'bucket': '710c830d-cdb5-4fc3-932c-755ef78b2cf3',
                'checksum': 'md5:a3854ba4564afdefc374781c8419f088',
                'key': 'article.pdf',
                'links': {
                    'self': 'https://zenodo.org/api/files/710c830d-cdb5-4fc3-932c-755ef78b2cf3/article.pdf',
                },
                'size': 346286,
                'type': 'pdf',
            },
        ],
        'id': 4308144,
        'links': {
            'badge': 'https://zenodo.org/badge/doi/10.32463/rphs.2018.v04i02.11.svg',
            'bucket': 'https://zenodo.org/api/files/710c830d-cdb5-4fc3-932c-755ef78b2cf3',
            'doi': 'https://doi.org/10.32463/rphs.2018.v04i02.11',
            'html': 'https://zenodo.org/record/4308144',
            'latest': 'https://zenodo.org/api/records/4308144',
            'latest_html': 'https://zenodo.org/record/4308144',
            'self': 'https://zenodo.org/api/records/4308144',
        },
        'metadata': {
            'access_right': 'open',
            'access_right_category': 'success',
            'creators': [
                {
                    'name': 'Gautam, Bikram',
                    'orcid': '0000-0002-8945-867X',
                },
                {
                    'name': 'Aryal, Lomas',
                },
                {
                    'name': 'Adhikari, Sachana',
                },
                {
                    'name': 'Rana, Manoj',
                },
                {
                    'name': 'Rajbhanshi, Anjita',
                },
                {
                    'name': 'Ghale, Sunita',
                },
                {
                    'name': 'Adhikari, Rameshwar',
                },
            ],
            'description': 'Background: Waste water contains microorganisms which are continuously shed in the feces. These microorganisms especially bacteria might acquire antibiotic resistance and pose a significant threat to human health. Therefore, this work aims at isolating bacteriophage capable of infecting the isolated bacteria. Methodology: For this purpose, the grab sampling was performed at the Guheswori sewage treatment plant from the inlet in the primary treatment plant and from the outlet of the secondary treatment plant. For the isolation of bacteriophage, bacteriophage in the sewage was first enriched in an isolated pathogen, then filtered and then subjected to the isolates in the nutrient agar. Results: Pathogens like Escherichia coli, Salmonella Typhi, Enterococcus faecalis, Staphylococcus aureus, Coagulase negative Staphylococcus (CONS), Citrobacter fruendii, Enterobacter aerogenes, Proteus mirabilis, P. vulgaris, Pseudomonas aeruginosa were screened. Bacteriophage was able to infect E. coli (p &lt; 0.001), S. Typhi (p &lt; 0.001), E. faecalis (p = 0.182); and unable to infect S. aureus, CONS, C. fruendii, E. aerogenes, P. mirabilis, P. vulgaris, P. aeruginosa. Conclusion: Bacteriophage are able to infect and kill pathogens like E. coli, S. Typhi, E. faecalis and unable to infect S. aureus, CONS, C. fruendii, E. aerogenes, P. mirabilis, P. vulgaris, P. aeruginosa. Among all other reasons of lowering bacterial load, bacteriophages could also be one of the confounding factor. Such bacteriophage able to infect and undergo lytic cycle could be used in phage typing.',
            'doi': '10.32463/rphs.2018.v04i02.11',
            'license': {
                'id': 'CC-BY-4.0',
            },
            'publication_date': '2018-05-15',
            'relations': {
                'version': [
                    {
                        'count': 1,
                        'index': 0,
                        'is_last': True,
                        'last_child': {'pid_type': 'recid', 'pid_value': '4308144'},
                        'parent': {'pid_type': 'recid', 'pid_value': '4308143'},
                    },
                ],
            },
            'resource_type': {
                'subtype': 'article',
                'title': 'Journal article',
                'type': 'publication',
            },
            'title': 'Isolation of Bacteriophage from Guheswori Sewage Treatment Plant Capable of Infecting Pathogens',
        },
        'owners': [13380],
        'revision': 2,
        'stats': {
            'downloads': 5.0,
            'unique_downloads': 5.0,
            'unique_views': 11.0,
            'version_downloads': 5.0,
            'version_unique_downloads': 5.0,
            'version_unique_views': 11.0,
            'version_views': 11.0,
            'version_volume': 1731430.0,
            'views': 11.0,
            'volume': 1731430.0,
        },
        'updated': '2020-12-06T12:27:08.762829+00:00',
    }

    return data


@pytest.mark.usefixtures('zenodo_protocol')
class TestZenodoProtocol(MetaTestProtocol):
    """
    Test class for zenodo protocol
    """

    @responses.activate
    def test_create_empty_publication(self):
        """
        Function must return a Zenodo id and send empty json
        """
        zenodo_id = 1
        responses.add(
            responses.POST,
            self.protocol.repository.endpoint,
            json={'id': zenodo_id},
            status=201,
        )
        
        r = self.protocol._create_empty_publication()

        assert responses.calls[0].request.headers.get('Content-Type') == 'application/json'
        assert responses.calls[0].request.body == bytes(json.dumps({}), 'utf-8')
        assert r == zenodo_id


    @responses.activate
    def test_create_empty_publication_fail(self):
        """
        Function must raise DepositError if something went wrong
        """
        zenodo_id = 1
        responses.add(
            responses.POST,
            self.protocol.repository.endpoint,
            json={'id': zenodo_id},
            status=500,
        )
        with pytest.raises(DepositError):
            self.protocol._create_empty_publication()

    def test_init_deposit_already_on_zenodo(self, dummy_oairecord, user_leibniz):
        paper = dummy_oairecord.about
        dummy_oairecord.splash_url = 'https://zenodo.org/record/4328519'
        dummy_oairecord.save()

        assert self.protocol.init_deposit(paper, user_leibniz) == False


    def test_get_metadata(self, upload_data, license_chooser):
        self.protocol.paper = upload_data.get('paper')

        # We prepare data for the form
        data = dict()
        if upload_data['oairecord'].description is not None:
            data['abstract'] = upload_data['oairecord'].description
        else:
            data['abstract'] = upload_data['abstract']
        data['license'] = license_chooser.pk

        form = self.protocol.get_bound_form(data)
        form.is_valid()

        metadata = self.protocol._get_metadata(form)
        # Nice thing is, that this protocol is static in terms of configuration, so that we can simply check against verified metadata
        f_name = os.path.join(settings.BASE_DIR, 'deposit', 'zenodo', 'test_data', '{}.json'.format(upload_data['load_name']))
        with open(f_name, 'r') as fin:
            expected_metadata = json.load(fin)

        assert metadata == expected_metadata

    def test_init_deposit_zenodo_oairecord(self, user_isaac_newton, dummy_oairecord, dummy_paper):
        """
        If there is a oairecord with zenodo in the splash url, function must return false
        """
        dummy_oairecord.splash_url = 'https://zenodo.org/record/50134'
        dummy_oairecord.save()

        result = self.protocol.init_deposit(dummy_paper, user_isaac_newton)
        assert result == False


    def test_submit_deposit_no_api_key(self, db):
        """
        If no api key is provided, we expect a deposit error
        """
        self.protocol.repository.api_key = None
        self.protocol.repository.save()

        with pytest.raises(DepositError):
            self.protocol.submit_deposit(None, None)

    def test_submit_deposit(self, blank_pdf_path, license_chooser, mock_doi, publish_response, requests_mocker):
        doi = '10.32463/rphs.2018.v04i02.11'
        self.protocol.paper = Paper.create_by_doi(doi)

        # We prepare data for the form
        data = {
            'abstract' : self.protocol.paper.oairecord_set.first().description,
            'license' : license_chooser.pk
        }

        form = self.protocol.get_bound_form(data)
        form.is_valid()

        zenodo_id = publish_response.get('id')
        # This is for creating the document
        requests_mocker.add(
            responses.POST,
            self.protocol.repository.endpoint,
            json={'id': zenodo_id},
            status=201,
        )
        # This for uploading file
        requests_mocker.add(
            responses.POST,
            '{}/{}/files'.format(self.protocol.repository.endpoint, zenodo_id),
            status=201,
        )
        # This is for submitting metadata
        requests_mocker.add(
            responses.PUT,
            self.protocol.repository.endpoint + '/{}'.format(zenodo_id),
            status=200,
        )
        # This is for publishing
        requests_mocker.add(
            responses.POST,
            self.protocol.repository.endpoint + '/{}/actions/publish'.format(zenodo_id),
            json=publish_response,
            status=202
        )
        dr = self.protocol.submit_deposit(blank_pdf_path, form)
        assert dr.identifier == zenodo_id
        assert dr.splash_url == publish_response.get('links').get('html')
        assert dr.pdf_url == publish_response.get('files')[0].get('links').get('self')

    @responses.activate
    def test_submit_metadata(self, metadata):
        """
        Function must put metadata to zenodo
        """
        zenodo_id = 1
        responses.add(responses.PUT, self.protocol.repository.endpoint + '/{}'.format(zenodo_id), status=200)

        self.protocol._submit_metadata(zenodo_id, metadata)

        assert responses.calls[0].request.headers.get('Content-Type') == 'application/json'


    @responses.activate
    def test_submit_metadata_fail(self, metadata):
        """
        Function must raise DepositError if something went wrong
        """
        zenodo_id = 1
        responses.add(responses.PUT, self.protocol.repository.endpoint + '/{}'.format(zenodo_id), status=500)

        with pytest.raises(DepositError):
            self.protocol._submit_metadata(zenodo_id, metadata)

    @responses.activate
    def test_publish(self, publish_response):
        """
        Function must return some json
        """
        zenodo_id = 1
        responses.add(
            responses.POST,
            self.protocol.repository.endpoint + '/{}/actions/publish'.format(zenodo_id),
            json=publish_response,
            status=202
        )
        r = self.protocol._publish(zenodo_id)

        assert r == publish_response

    @responses.activate
    def test_publish_fail(self):
        """
        Function must return some json
        """
        zenodo_id = 1
        responses.add(
            responses.POST,
            self.protocol.repository.endpoint + '/{}/actions/publish'.format(zenodo_id),
            status=400
        )

        with pytest.raises(DepositError):
            self.protocol._publish(zenodo_id)

    @responses.activate
    def test_upload_pdf(self, blank_pdf_path, book_god_of_the_labyrinth):
        self.protocol.paper = book_god_of_the_labyrinth
        zenodo_id = 1
        responses.add(
            responses.POST,
            self.protocol.repository.endpoint + '/{}/files'.format(zenodo_id),
            status=201,
        )

        self.protocol._upload_pdf(blank_pdf_path, zenodo_id)
        # Hard to test something here, so we just assume, the function doesn't do any error
