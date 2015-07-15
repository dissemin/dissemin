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
from StringIO import StringIO

from django.utils.translation import ugettext as _
from os.path import basename
#from backend.crossref import consolidate_publication
from dissemin.settings import ZENODO_KEY, DOI_PROXY_DOMAIN
from papers.errors import MetadataSourceException

class DepositError(Exception):
    def __init__(self, msg, logs):
        super(DepositError, self).__init__(msg)
        self.logs = logs

ZENODO_API_URL = "https://zenodo.org/api/deposit/depositions"

def fetch_zotero_by_DOI(doi):
    """
    Fetch Zotero metadata for a given DOI.
    Works only with the doi_cache proxy.
    """
    try:
        request = requests.get('http://'+DOI_PROXY_DOMAIN+'/zotero/'+doi)
        return request.json()
    except ValueError as e:
        raise MetadataSourceException('Error while fetching Zotero metadat:\nInvalid JSON response.\n'+
                'Error: '+str(e))

def consolidate_publication(publi):
    """
    Fetches the abstract from Zotero and adds it to the publication if it succeeds.
    """
    zotero = fetch_zotero_by_DOI(publi.doi)
    for item in zotero:
        if 'abstractNote' in item:
            publi.abstract = item['abstractNote']
            publi.save(update_fields=['abstract'])
    return publi


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

def createZenodoMetadata(paper):
    metadata = {}
    oairecords = paper.sorted_oai_records
    publications = paper.publication_set.all()

    # Document type
    dt = swordDocumentType(paper)
    metadata['upload_type'] = dt[0]
    if dt[0] == 'publication':
        metadata['publication_type'] = dt[1]

    # Publication date
    metadata['publication_date'] = paper.pubdate.isoformat()

    # Title
    metadata['title'] = paper.title

    # Creators
    def formatAuthor(author):
        res = {'name':author.name.last+', '+author.name.first}
        if author.researcher and author.researcher.orcid:
            res['orcid'] = author.researcher.orcid
        # TODO: affiliation
        return res
    metadata['creators'] = map(formatAuthor, paper.sorted_authors)

    # Abstract
    abstract = ''
    for record in oairecords:
        if record.description and len(record.description) > len(abstract):
            abstract = record.description

    if len(abstract) < 32: # that's really short for an abstract !
        for publi in publications:
            print "Consolidating!"
            publi = consolidate_publication(publi)
            if publi.abstract and len(publi.abstract) > len(abstract):
                abstract = publi.abstract
                break

    metadata['description'] = abstract

    # Access right: TODO

    # License: TODO

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

    # Keywords TODO (this involves having separated keywords in OAI records.)

    # Notes TODO
    # metadata['notes'] = 'Uploaded by dissem.in on behalf of ' …

    # Related identifiers
    idents = map(lambda r: {'relation':'isAlternateIdentifier','identifier':r.splash_url}, oairecords)
    for publi in publications:
        if publi.journal and publi.journal.issn:
            idents.append({'relation':'isPartOf','identifier':publi.journal.issn})
    
    data = {"metadata": metadata}
    return data

def submitPubli(paper,filePdf):
    result = {}
    log = ''
    def log_request(r, expected_status_code, error_msg, log):
        log += '--- Request to %s\n' % r.url
        log += 'Status code: %d (expected %d)\n' % (r.status_code, expected_status_code)
        if r.status_code != expected_status_code:
            log += 'Server response:\n'
            log += r.text
            log += '\n'
            raise DepositError(error_msg, log)
        return log

    if ZENODO_KEY is None:
        raise DepositError("No Zenodo API key provided.")

    try:
        # Checking the access token
        log += "### Checking the access token\n"
        r = requests.get(ZENODO_API_URL+"?access_token=" + ZENODO_KEY)
        log = log_request(r, 200, 'Unable to authenticate to Zenodo.', log)
           
        # Creating a new deposition
        log += "### Creating a new deposition\n"
        headers = {"Content-Type": "application/json"}
        r = requests.post(ZENODO_API_URL+"?access_token=" + ZENODO_KEY , data=str("{}"), headers=headers)
        log = log_request(r, 201, 'Unable to create a new deposition on Zenodo.', log)
        deposition_id = r.json()['id']
        result['identifier'] = deposition_id
        log += "Deposition id: %d\n" % deposition_id

        # Uploading the PDF
        log += "### Uploading the PDF\n"
        data = {'filename':basename(filePdf)}
        files = {'file': open(filePdf, 'rb')}
        r = requests.post(ZENODO_API_URL+"/%s/files?access_token=%s" % (deposition_id,ZENODO_KEY), data=data, files=files)
        log = log_request(r, 201, 'Unable to send the document to Zenodo.', log)

        # Creating the metadata
        log += "### Generating the metadata\n"
        data = createZenodoMetadata(paper)
        log += json.dumps(data, indent=4)+'\n'

        # Submitting the metadata
        log += "### Submitting the metadata\n"
        r = requests.put(ZENODO_API_URL+"/%s?access_token=%s" % ( deposition_id, ZENODO_KEY), data=json.dumps(data), headers=headers)
        log = log_request(r, 200, 'Unable to submit paper metadata to Zenodo.', log)
        
        # Deleting the deposition
        log += "### Deleting the deposition\n"
        r = requests.delete(ZENODO_API_URL+"/%s?access_token=%s" % ( deposition_id, ZENODO_KEY) )
    #    r = requests.post("https://zenodo.org/api/deposit/depositions/%s/actions/publish?access_token=2SsQE9VkkgDQG1WDjrvrZqTJtkmsGHICEaccBY6iAEuBlSTdMC6QvcTR2HRv" % deposition_id)
    #   print(r.status_code)
    except DepositError as e:
        raise e
    except Exception as e:
        log += "Caught exception:\n"
        log += str(type(e))+': '+str(e)+'\n'
        log += traceback.format_exc()
        log += '\n'
        raise DepositError('Connection to Zenodo failed. Please try again later.', log)

    result['logs'] = log
    return result
