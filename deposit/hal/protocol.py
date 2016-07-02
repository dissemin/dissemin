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
import traceback, sys
from io import BytesIO
from zipfile import ZipFile

from django.utils.translation import ugettext as __
from django.utils.translation import ugettext_lazy as _
from os.path import basename

from deposit.protocol import *
from deposit.registry import *

from deposit.hal.forms import *
from deposit.hal.metadataFormatter import *

from papers.errors import MetadataSourceException
from papers.utils import kill_html

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1


import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


class HALProtocol(RepositoryProtocol):
    """
    A protocol to submit using the HAL SWORD API
    """
    def __init__(self, repository, **kwargs):
        super(HALProtocol, self).__init__(repository, **kwargs)
        # We let the interface define another API endpoint (sandbox…)
        self.api_url = repository.endpoint
        if not self.api_url:
            self.api_url = "https://api.archives-ouvertes.fr/sword/hal/"
        self.username = repository.username
        self.password = repository.password
        print self.user
        print self.password

    def predict_topic(self, topic_text):
        if not topic_text:
            return
        try:
            r = requests.post('http://haltopics.dissem.in:6377/predict', data={'text':topic_text})
            return r.json()['decision']['code']
        except (requests.RequestsException, ValueError, KeyError) as e:
            print e
            return None

    def get_form(self):
        data = {}
        data['paper_id'] = self.paper.id
        
        # Abstract
        if self.paper.abstract:
            data['abstract'] = kill_html(self.paper.abstract)
        else:
            self.paper.consolidate_metadata(wait=False)

        # Topic
        topic_text = ''
        if 'abstract' in data:
            topic_text = data['abstract']
        else:
            topic_text = self.paper.title
        
        return HALForm(initial=data)

    def get_bound_form(self, data):
        return HALForm(data)

    def create_zip(self, pdf, metadata):
        s = BytesIO()
        with ZipFile(s, 'w') as zipFile:
            zipFile.writestr("article.pdf", str(pdf))
            zipFile.writestr("meta.xml", str(metadata))

        with open('/tmp/hal.zip', 'wb') as f:
            with ZipFile(f, 'w') as zipFile:
                zipFile.writestr("article.pdf", str(pdf))
                zipFile.writestr("meta.xml", str(metadata))
        return s

    def encodeUserData(self):
        return "Basic " + (self.username + ":" + self.password
                ).encode("base64").rstrip()

    def submit_deposit(self, pdf, form):
        result = {}
        if self.username is None or self.password is None:
            raise DepositError(__("No HAL user credentials provided."))

        deposit_result = DepositResult()

        try:
            # Creating the metadata
            self.log("### Generating metadata")
            metadata = self.createMetadata(form)
            # TODO dump XML

            # Check that there is an abstract
            #if data['metadata'].get('description','') == '':
            #    self.log('No abstract found, aborting.')
            #    raise DepositError(__('No abstract is available for this paper but '+
            #            'Zenodo requires to attach one. Please use the metadata panel to provide one.'))

            # Bundling the metadata and the PDF
            self.log("### Creating ZIP file")
            zipFile = self.create_zip(pdf, metadata)

            # Creating a new deposition
            self.log("### Creating a new deposition")

            host = 'api-preprod.archives-ouvertes.fr'
            conn = http_client.HTTPConnection(host)
            conn.putrequest('POST', '/sword/hal', True, True)
            zipContent = zipFile.getvalue() 
            headers = {
                'Authorization': self.encodeUserData(),
                'Host': host,
                'X-Packaging':'http://purl.org/net/sword-types/AOfr',
                'Content-Type':'application/zip',
                'Content-Disposition': 'attachment; filename=meta.xml',
                'Content-Length': len(zipContent),
                }
            for header, value in headers.items():
                conn.putheader(header, value)
            conn.endheaders()
            conn.send(zipContent)
            resp = conn.getresponse()
            print resp.read()
            deposition_id = resp.getheader('location')

            if False:
                files = {'file':('deposit.zip',zipfile,'application/zip')}
                headers = {"x-packaging":"http://purl.org/net/sword-types/aofr"}
                r = requests.post(self.api_url,
                        headers=headers,
                        files=files,
                        auth=(self.username,self.password))
                self.log(unicode(r.request.headers))
                self.log(unicode(r.headers))
                print "result"
                print r.body
                self.log_request(r, 201, __('unable to create a new deposition on hal.'))
                deposition_id = r.headers['location']


            deposit_result.identifier = deposition_id
            self.log("Deposition id: %s" % deposition_id)

            deposit_result.splash_url = deposition_id
            deposit_result.pdf_url = deposit_result.splash_url + '/document'

        except DepositError as e:
            raise e
        except Exception as e:
            self.log("Caught exception:")
            self.log(str(type(e))+': '+str(e)+'')
            self.log(traceback.format_exc())
            raise DepositError('Connection to HAL failed. Please try again later.')

        return deposit_result

    def createMetadata(self, form):
        formatter = AOFRFormatter()
        metadata = formatter.toString(self.paper, 'article.pdf', True)
        return metadata

protocol_registry.register(HALProtocol)

