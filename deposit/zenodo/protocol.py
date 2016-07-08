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

import json
import requests
from StringIO import StringIO

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from os.path import basename

ZENODO_LICENSES_CHOICES = [
   ('cc-zero',
        _('Creative Commons CCZero (CC0)')),
   ('cc-by',
        _('Creative Commons Attribution (CC-BY)')),
   ('cc-by-sa',
        _('Creative Commons Attribution-ShareAlike (CC-BY-SA)')),
   ('cc-by-nc-4.0',
        _('Creative Commons Attribution-NonCommercial (CC-BY-NC)')),
   ('cc-by-nd-4.0',
        _('Creative Commons Attribution-NoDerivatives (CC-BY-ND)')),
   ('other-open',
        _('Other open license')),
 ]

from deposit.protocol import *
from deposit.registry import *
from deposit.zenodo.forms import *

from papers.errors import MetadataSourceException
from papers.utils import kill_html


class ZenodoProtocol(RepositoryProtocol):
    """
    A protocol to submit using the Zenodo API
    """
    def __init__(self, repository, **kwargs):
        super(ZenodoProtocol, self).__init__(repository, **kwargs)
        # We let the interface define another API endpoint (sandbox…)
        self.api_url = repository.endpoint
        if not self.api_url:
            self.api_url = "https://zenodo.org/api/deposit/depositions"

    def get_form(self):
        data = {}
        data['license'] = 'other-open'
        data['paper_id'] = self.paper.id
        if self.paper.abstract:
            data['abstract'] = kill_html(self.paper.abstract)
        else:
            self.paper.consolidate_metadata(wait=False)
        return ZenodoForm(initial=data)

    def get_bound_form(self, data):
        return ZenodoForm(data)

    def submit_deposit(self, pdf, form):
        result = {}

        if self.repository.api_key is None:
            raise DepositError(__("No Zenodo API key provided."))
        api_key = self.repository.api_key
        api_url_with_key = self.api_url+'?access_token='+api_key

        deposit_result = DepositResult()

        # Checking the access token
        self.log("### Checking the access token")
        r = requests.get(api_url_with_key)
        self.log_request(r, 200, __('Unable to authenticate to Zenodo.'))

        # Creating a new deposition
        self.log("### Creating a new deposition")
        headers = {"Content-Type": "application/json"}
        r = requests.post(api_url_with_key, data=str("{}"), headers=headers)
        self.log_request(r, 201, __('Unable to create a new deposition on Zenodo.'))
        deposition_id = r.json()['id']
        deposit_result.identifier = deposition_id
        self.log("Deposition id: %d" % deposition_id)

        # Uploading the PDF
        self.log("### Uploading the PDF")
        data = {'filename':'article.pdf'}
        files = {'file': open(pdf, 'rb')}
        r = requests.post(self.api_url+"/%s/files?access_token=%s" % (deposition_id,api_key),
                data=data, files=files)
        self.log_request(r, 201, __('Unable to transfer the document to Zenodo.'))

        # Creating the metadata
        self.log("### Generating the metadata")
        data = self.createMetadata(form)
        self.log(json.dumps(data, indent=4)+'')

        # Check that there is an abstract
        if data['metadata'].get('description','') == '':
            self.log('No abstract found, aborting.')
            raise DepositError(__('No abstract is available for this paper but '+
                    'Zenodo requires to attach one. Please use the metadata panel to provide one.'))

        # Submitting the metadata
        self.log("### Submitting the metadata")
        r = requests.put(self.api_url+"/%s?access_token=%s" % ( deposition_id, api_key),
                data=json.dumps(data), headers=headers)
        self.log_request(r, 200, __('Unable to submit paper metadata to Zenodo.'))

        if dry_run:
            # Deleting the deposition
            self.log("### Deleting the deposition")
            r = requests.delete(self.api_url+"/%s?access_token=%s" % ( deposition_id, api_key) )
            self.log(r.text)
            deposit_result.status = 'DRY_SUCCESS'

        else:
            self.log("### Publishing the deposition")
            r = requests.post(self.api_url+"/%s/actions/publish?access_token=%s" % (deposition_id, api_key))
            self.log_request(r, 202, __('Unable to publish the deposition on Zenodo.'))
            self.log(r.text)

            deposition_object = r.json()
            deposit_result.splash_url = deposition_object['record_url']
            deposit_result.pdf_url = deposit_result.splash_url + '/files/article.pdf'

        return deposit_result

    def createMetadata(self, form):
        metadata = {}
        oairecords = self.paper.sorted_oai_records
        publications = self.paper.publications

        # Document type
        dt = swordDocumentType(self.paper)
        metadata['upload_type'] = dt[0]
        if dt[0] == 'publication':
            metadata['publication_type'] = dt[1]

        # Publication date
        metadata['publication_date'] = self.paper.pubdate.isoformat()

        # Title
        metadata['title'] = self.paper.title

        # Creators
        def formatAuthor(author):
            res = {'name':author.name.last+', '+author.name.first}
            if author.researcher and author.researcher.orcid:
                res['orcid'] = author.researcher.orcid
            # TODO: affiliation
            return res
        metadata['creators'] = map(formatAuthor, self.paper.authors)

        # Abstract
        # If we are currently fetching the abstract, wait for the task to complete
        if self.paper.task:
            self.paper.consolidate_metadata(wait=True)
        abstract = form.cleaned_data['abstract'] or kill_html(self.paper.abstract)

        metadata['description'] = abstract

        # Access right: TODO

        # License
        metadata['license'] = form.cleaned_data['license']

        # Embargo date: TODO

        # DOI
        for publi in publications:
            metadata['doi'] = publi.doi
            if publi.pubdate:
                metadata['publication_date'] = publi.pubdate.isoformat()
                if publi.journal:
                    metadata['journal_title'] = publi.journal.title
                else:
                    metadata['journal_title'] = publi.title
                if publi.volume:
                    metadata['journal_volume'] = publi.volume
                if publi.issue:
                    metadata['journal_issue'] = publi.issue
                if publi.pages:
                    metadata['journal_pages'] = publi.pages
                if publi.container:
                    metadata['conference_title'] = publi.container
                break

        # Related identifiers
        idents = map(lambda r: {'relation':'isAlternateIdentifier','identifier':r.splash_url}, oairecords)
        for publi in publications:
            if publi.journal and publi.journal.issn:
                idents.append({'relation':'isPartOf','identifier':publi.journal.issn})

        data = {"metadata": metadata}
        return data

protocol_registry.register(ZenodoProtocol)

def swordDocumentType(paper):
    tr = {
            'journal-article':('publication','article'),
            'proceedings-article':('publication','conferencepaper'),
            'book-chapter':('publication','section'),
            'book':('publication','book'),
            'journal-issue':('publication','book'),
            'proceedings':('publication','book'),
            'reference-entry':('publication','other'),
            'poster':('poster',),
            'report':('publication','report'),
            'thesis':('publication','thesis'),
            'dataset':('dataset',),
            'preprint':('publication','preprint'),
            'other':('publication','other'),
         }
    return tr[paper.doctype]


