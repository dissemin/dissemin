from __future__ import unicode_literals

print "importing swordProtocol.py"

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


import deposit.sword.metadataFormatter as mdf
import papers.models as models
import requests
import lxml
from requests.auth import HTTPBasicAuth

#debug to true WILL print authentication credentials in the log file
debug = True

enforce_specification = True

randomPaper = models.Paper.objects.get(pk=1)
xmlModel=mdf.DCFormatter()
xmlCreated = xmlModel.toString(randomPaper,pretty=True)

atom_uri = 'http://www.w3.org/2005/Atom'
sword_uri = "http://purl.org/net/sword/terms/"
xmlns_uri = 'http://www.w3.org/2007/app'
rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
oai_uri = "http://www.openarchives.org/ore/terms/"
dc_uri = "http://purl.org/dc/terms/"
xmlns = '{%s}' % xmlns_uri
app = '{%s}' % xmlns_uri
sword = '{%s}' % sword_uri
rdf = '{%s}' % rdf_uri
atom = '{%s}' % atom_uri
dcterms = '{%s}' % dc_uri
ore = '{%s}' % oai_uri
nsmap = {None: xmlns_uri,
         'app': xmlns_uri,
         'sword': sword_uri,
         'atom': atom_uri,
         'dcterms': dc_uri,
         'ore': oai_uri,
         'rdf': rdf_uri}

dspace = Repository( name = "DSpaceDemo",
                     description = "demodespace",
                     url = "http://demo.dspace.org",
                     protocol="swordv2",
                     username="dspacedemo+admin@gmail.com",
                     password="dspace",
                     endpoint="http://demo.dspace.org/swordv2/servicedocument")

class Sword2Protocol(RepositoryProtocol):
    """SWORD2 Uploader
    When a user starts a deposit it will create :

    - self.paper = paper

    - self.user = user

    #TODO doc

    """

    def get_conn(self):
        """Connect repository.endpoint with the credentials and get the
        service document. Verify soundness of the service document.

        """

        atom_uri = 'http://www.w3.org/2005/Atom'
        sword_uri = "http://purl.org/net/sword/terms/"
        xmlns_uri = 'http://www.w3.org/2007/app'
        rdf_uri = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        oai_uri = "http://www.openarchives.org/ore/terms/"
        dc_uri = "http://purl.org/dc/terms/"
        xmlns = '{%s}' % xmlns_uri
        app = '{%s}' % xmlns_uri
        sword = '{%s}' % sword_uri
        rdf = '{%s}' % rdf_uri
        atom = '{%s}' % atom_uri
        dcterms = '{%s}' % dc_uri
        ore = '{%s}' % oai_uri
        nsmap = {None: xmlns_uri,
                 'app': xmlns_uri,
                 'sword': sword_uri,
                 'atom': atom_uri,
                 'dcterms': dc_uri,
                 'ore': oai_uri,
                 'rdf': rdf_uri}

        if debug:
            errorMsg = "Prepare a connexion for %s" % (self.repository.endpoint)
            errorMsg = "%s with username [ %s ] and password [ %s ]" % (errorMsg,
                                                                        self.repository.username,
                                                                        self.repository.password)
            self.log(errorMsg)
        if self.repository.endpoint is None:
            raise DepositError(__("No repository endpoint given."))
        if self.repository.username is None:
            raise DepositError(__("No username given to connect to the endpoint,"))
        if self.repository.password is None:
            raise DepositError(__("No password given to connect to the endpoint,"))
        self.credential = HTTPBasicAuth(self.repository.username,
                                      self.repository.password)
        self.servicedocument = requests.get(self.repository.endpoint, auth=self.credential)
        self.xml_response = etree.fromstring(self.servicedocument.content)
        #check for status code 200 is not enough (specification)
        self.log(self.servicedocument.text)
        if (enforce_specification):
            # We assume [service] is the root. I did not find if the spec enforces that too
            if self.xml_response.tag != ("{%s}service"%nsmap['app']):
                raise DepositError(__("The document sent back from the server is not an xml starting with service"))
            #The SWORD server MUST specify the sword:version element with a value of 2.0 [SWORD003]
            #as a child of the app:service element.
            self.version_here = False
            for i in self.xml_response.iterchildren():
                if ((i.tag == ("{%s}version"%nsmap['sword'])) & (i.text == "2.0")):
                    self.version_here = True
            if not(self.version_here):
                raise DepositError(__("We could not check that the server use SWORD 2 (sword:version is 2.0). (MUST in the spec)"))
            # If we see several maxUploadSize we take the last one. Unspecified in the spec?
            self.maxUploadSize = None
            for i in self.xml_response.iterchildren():
                if i.tag == ("{%s}maxUploadSize"%nsmap['sword']) :
                    try:
                        self.maxUploadSize = int(i.text)
                    except ValueError:
                        raise DepositError(__("maxUploadSize did not contain an integer. (MUST in the spec)"))
            # Check for the accept format for every collection
            self.acceptValue = {}
            self.acceptValueMultipart = {}
            for i in self.xml_response.findall(".//app:collection",namespaces=nsmap):
                self.acceptValue[i] = None
                self.acceptValueMultipart[i] = None                
                accept= i.findall(".//app:accept",namespaces=nsmap)
                for l in accept :
                    attribute=l.get("alternate")
                    if attribute==None:
                        self.acceptValue[i]=l.text
                    if attribute=="multipart-related":
                        self.acceptValueMultipart[i]=l.text
                if (self.acceptValue[i]==None):
                    raise DepositError(__("accept without multipart-related missing (MUST in the spec)"))
                if self.acceptValueMultipart[i]==None:
                    raise DepositError(__("accept with multipart-related missing (MUST in the spec)"))
                # we should check that it follows the recommendation as well?

            # We assume mediation is false for now.

            # Get acceptPackaging

            # The client SHOULD NOT attempt to deposit files with a packaging format that is not in the sword:acceptPackaging elements, although the client MAY specify the binary package format (see Section 5: IRIs and Section 7: Packaging for more details) in order to deposit opaquely packaged content

        return None

    def modify_deposit(self):
        return None

    def delete_deposit(self):
        return None

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


    def get_form(self):
        """ Feedback system with the user """
        data = {}
        data['paper_id'] = self.paper.id
        if self.paper.abstract:
            data['abstract'] = kill_html(self.paper.abstract)
        else:
            self.paper.consolidate_metadata(wait=False)
        return BaseMetadataForm(initial=data)

    def get_bound_form(self, data):
        """
        return BaseMetadataForm(data)
        """


    def submit_deposit(self, pdf, form):
        result = {}

        print "Submit deposit"
        conn = None
        try:
            self.log("### Initiate connection")
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
protocol_registry.register(Sword2Protocol)
