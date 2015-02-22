# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals

from urllib2 import urlopen, HTTPError, URLError
from urllib import urlencode
import xml.etree.ElementTree as ET
import unicodedata

from papers.models import *
from papers.errors import MetadataSourceException
from papers.utils import nstrip

romeo_api_key = open('romeo_api_key').read().strip()

def find_journal_in_model(search_terms):
    issn = search_terms.get('issn', None)
    title = search_terms.get('jtitle', None)
    # Look up the journal in the model
    # By ISSN
    if issn:
        matches = Journal.objects.filter(issn=issn)
        if matches:
            return matches[0]

    # By title
    if title:
        matches = Journal.objects.filter(title__iexact=title)
        if matches:
            return matches[0]


def fetch_journal(search_terms, matching_mode='exact'):
    """
    Fetch the journal data from RoMEO. Returns an Journal object.
    search_terms should be a dictionnary object containing at least one of these fields:
    """
    allowed_fields = ['issn', 'jtitle']
    original_search_terms = search_terms.copy()

    # Check the arguments
    if not all(map(lambda x: x in allowed_fields, (key for key in search_terms))):
        raise ValueError('The search terms have to belong to '+str(allowed_fields)+
                'but the dictionary I got is '+str(search_terms))

    # Remove diacritics (because it has to be sent in ASCII to ROMEO)
    for key in search_terms:
        search_terms[key] = unicodedata.normalize('NFKD',search_terms[key]).encode('ASCII', 'ignore')

    # First check we don't have it already
    journal = find_journal_in_model(search_terms)
    if journal:
        return journal

    # Prepare the query
    if romeo_api_key:
        search_terms['ak'] = romeo_api_key
    request = 'http://sherpa.ac.uk/romeo/api29.php?'+urlencode(search_terms)

    # Perform the query
    try:
        response = urlopen(request).read()
    except URLError as e:
        raise MetadataSourceException('Error while querying RoMEO.\n'+
                'URL was: '+request+'\n'
                'Error is: '+str(e))

    # Parse it
    try:
        root = ET.fromstring(response)
    except ET.ParseError as e:
        raise MetadataSourceException('RoMEO returned an invalid XML response.\n'+
                'URL was: '+request+'\n'
                'Error is: '+str(e))

    # Find the matching journals (if any)
    journals = list(root.findall('./journals/journal'))
    if not journals:
        # Retry with a less restrictive matching type
        if matching_mode == 'exact':
            return fetch_journal(original_search_terms, 'contains')
        # TODO do it also with 'contains' but with a disambiguation notice
        return None
    if len(journals) > 1:
        print ("Warning, "+str(len(journals))+" journals match the RoMEO request, "+
                "defaulting to the first one")
        # TODO different behaviour: get the ISSN and try again.
    journal = journals[0]

    names = list(journal.findall('./jtitle'))
    if not names:
        raise MetadataSourceException('RoMEO returned a journal without title.\n'+
                'URL was: '+request)
    if len(names) > 1:
        print("Warning, "+str(len(names))+" names provided for one journal, "+
                "defaulting to the first one")
    name = names[0].text
    
    issn = None
    try:
        issn = nstrip(journal.findall('./issn')[0].text)
    except KeyError, IndexError:
        pass

    # Now we may have additional info, so it's worth trying again in the model
    model_journal = find_journal_in_model({'issn':issn,'jtitle':name})
    if model_journal:
        return model_journal

    # Otherwise we need to find the publisher
    publishers = root.findall('./publishers/publisher')
    if not publishers:
        return None
    # TODO here we shouldn't default to the first one but look it up using the <romeopub>
    publisher_desc = publishers[0]

    publisher = get_or_create_publisher(publisher_desc)

    result = Journal(title=name,issn=issn,publisher=publisher)
    result.save()
    return result

def get_or_create_publisher(romeo_xml_description):
    """
    Retrieves from the model, or creates into the model,
    the publisher corresponding to the <publisher> description
    from RoMEO
    """
    xml = romeo_xml_description
    romeo_id = None
    try:
        romeo_id = xml.attrib['id']
    except KeyError:
        raise MetadataSourceException('RoMEO did not provide a publisher id.\n'+
                'URL was: '+request)
    
    name = None
    try:
        name = xml.findall('./name')[0].text.strip()
    except (KeyError, IndexError, AttributeError):
        raise MetadataSourceException('RoMEO did not provide the publisher\'s name.\n'+
                'URL was: '+request)

    alias = None
    try:
        alias = nstrip(xml.findall('./alias')[0].text)
    except KeyError, IndexError:
        pass

    # Check if we already have it
    matches = None
    if alias:
        matches = Publisher.objects.filter(romeo_id=romeo_id, name__iexact=name,alias__iexact=alias)
    else:
        matches = Publisher.objects.filter(romeo_id=romeo_id, name__iexact=name,alias__isnull=True)
    if matches:
        return matches[0]

    # Otherwise, create it
    url = None
    try:
        url = nstrip(xml.findall('./homeurl')[0].text)
    except KeyError, IndexError:
        pass

    preprint = None
    try:
        preprint = xml.findall('./preprints/prearchiving')[0].text.strip()
    except (KeyError, IndexError, AttributeError):
        raise MetadataSourceException('RoMEO did not provide the preprint policy.\n'+
                'URL was: '+request)

    postprint = None
    try:
        postprint = xml.findall('./postprints/postarchiving')[0].text.strip()
    except (KeyError, IndexError, AttributeError):
        raise MetadataSourceException('RoMEO did not provide the postprint policy.\n'+
                'URL was: '+request)

    pdfversion = None
    try:
        pdfversion = xml.findall('./pdfversion/pdfarchiving')[0].text.strip()
    except (KeyError, IndexError, AttributeError):
        raise MetadataSourceException('RoMEO did not provide the pdf archiving policy.\n'+
                'URL was: '+request)

    # Compute OA status of the publisher
    status = 'UNK'
    if xml.attrib.get('id') == 'DOAJ':
        status = 'OA'
    if preprint == 'can' or postprint == 'can' or pdfversion == 'can':
        status = 'OK'
    elif preprint == 'cannot' and postprint == 'cannot' and pdfversion == 'cannot':
        status = 'NOK'

    publisher = Publisher(name=name, alias=alias, url=url, preprint=preprint,
            postprint=postprint, pdfversion=pdfversion, romeo_id=romeo_id,
            oa_status=status)
    publisher.save()

    # Add the conditions, restrictions, and copyright
    for restriction in xml.findall('./preprints/prerestrictions/prerestriction'):
        addRestriction(restriction, 'preprint', publisher)

    for restriction in xml.findall('./postprints/postrestrictions/postrestriction'):
        addRestriction(restriction, 'postprint', publisher)

    for restriction in xml.findall('./pdfversion/pdfrestrictions/pdfrestriction'):
        addRestriction(restriction, 'pdfversion', publisher)

    for condition in xml.findall('./conditions/condition'):
        if condition.text:
            c = PublisherCondition(publisher=publisher, text=condition.text.strip())
            c.save()
            if c.text.lower() == 'all titles are open access journals':
                publisher.status = 'OA'
                publisher.save(update_fields=['oa_status'])
    
    for link in xml.findall('./copyrightlinks/copyrightlink'):
        text = None
        url = None
        texts = link.findall('./copyrightlinktext')
        if texts:
            text = nstrip(texts[0].text)
        urls = link.findall('./copyrightlinkurl')
        if urls:
            url = nstrip(urls[0].text)
        if url and text:
            cplink = PublisherCopyrightLink(text=text, url=url, publisher=publisher)
            cplink.save()

    return publisher

def addRestriction(xml, applies_to, publisher):
    text = nstrip(xml.text)
    if text:
        print "Adding restriction "+text
        r = PublisherRestrictionDetail(publisher=publisher, applies_to=applies_to, text=text)
        r.save()

