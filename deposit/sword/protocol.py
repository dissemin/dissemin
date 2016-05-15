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

print "importing protocol.py"

import json
import requests 
import traceback, sys
from StringIO import StringIO

from django.utils.translation import ugettext as __
from django.utils.translation import ugettext_lazy as _
from os.path import basename

from deposit.protocol import *
from deposit.forms import *
from deposit.sword import metadataFormatter

from papers.errors import MetadataSourceException
from papers.utils import kill_html

from django.conf import settings

import sword2

class SwordProtocol(RepositoryProtocol):
    """
    A generic SWORD protocol using the sword2 library
    """
    def get_conn(self):
        if self.repository.endpoint is None:
            raise DepositError(__("No servicedocument provided."))
        return sword2.Connection(self.repository.endpoint,
                user_name=self.repository.username,
                user_pass=self.repository.password)


    def get_form(self):
        data = {}
        data['paper_id'] = self.paper.id
        if self.paper.abstract:
            data['abstract'] = kill_html(self.paper.abstract)
        else:
            self.paper.consolidate_metadata(wait=False)
        return BaseMetadataForm(initial=data)

    def get_bound_form(self, data):
        return BaseMetadataForm(data)

    def createMetadata(self, form):
        entry = sword2.Entry()
        p = self.paper
        entry.add_field('title', p.title)
        for a in p.authors:
            if a.orcid:
                entry.add_author(unicode(a), uri='http://{}/{}'.format(settings.ORCID_BASE_DOMAIN, a.orcid))
            else:
                entry.add_author(unicode(a))
        if p.abstract:
            entry.add_field('dcterms_abstract', p.abstract)
        entry.add_field('dcterms_issued', p.pubdate.isoformat())
        for pub in p.publications:
            entry.add_field('dcterms_identifier', 'doi:'+pub.doi)
            if pub.journal and pub.journal.issn:
                entry.add_field('dcterms_isPartOf', 'issn:'+pub.journal.issn)

        for rec in p.oairecords:
            entry.add_field('dcterms_source', rec.splash_url)

        entry.add_field('dcterms_type', p.doctype)

        return entry

    def submit_deposit(self, pdf, form):
        result = {}

        print "Submit deposit"
        conn = None
        try:
            self.log("### Connecting")
            conn = self.get_conn()
            self.log("### Creating metadata")
            #entry = self.createMetadata(form)
            #self.log(entry.pretty_print())

            formatter = DCFormatter()
            meta = formatter.toString(self.paper, 'article.pdf', True)
            print meta
            self.log(meta)

            f = StringIO(pdf)
            self.log("### Submitting metadata")
            #receipt = conn.create(metadata_entry=entry,mimetype="application/pdf",
            #        payload=f,col_iri=self.repository.api_key)
            #receipt = conn.create(metadata_entry=entry,col_iri=self.repository.api_key)
            files = {'file':('metadata.xml',meta)}
            headers = {'In-Progress':'false', 'Content-Type': 'application/atom+xml; type=entry'}
            auth = requests.auth.HTTPBasicAuth(self.repository.username,self.repository.password)
            r = requests.post(self.repository.api_key, files=files, headers=headers,
                    auth=auth)
            self.log_request(r, 201, __('Unable to submit the paper to the collection.'))

            self.log(unicode(r.text))

            deposit_result = DepositResult()
        except requests.exceptions.RequestException as e:
            raise DepositError(unicode(e))
        except sword2.exceptions.HTTPResponseError as e:
            if conn is not None:
                self.log(unicode(conn.history))
            raise DepositError(__('Failed to connect to the SWORD server.'))

        return deposit_result

from deposit.registry import *
protocol_registry.register(SwordProtocol)

