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

import lxml.etree as ET
from io import StringIO, BytesIO

import requests
import requests.exceptions

from papers.models import *
from papers.errors import MetadataSourceException
from papers.utils import nstrip, remove_diacritics
from backend.utils import urlopen_retry

from publishers.models import *

from dissemin.settings import ROMEO_API_KEY


# Minimum number of times we have seen a publisher name
# associated to a publisher to assign this publisher
# to publications where the journal was not found.
# (when this name has only been associated to one publisher)
PUBLISHER_NAME_ASSOCIATION_THRESHOLD = 10

# Minimum ratio between the most commonly matched journal
# and the second one
PUBLISHER_NAME_ASSOCIATION_FACTOR = 4

def perform_romeo_query(search_terms):
    search_terms = search_terms.copy()
    if ROMEO_API_KEY:
        search_terms['ak'] = ROMEO_API_KEY
    base_url = 'http://sherpa.ac.uk/romeo/api29.php'

    # Perform the query
    try:
        response = urlopen_retry(base_url, data=search_terms).encode('utf-8')
    except requests.exceptions.RequestException as e:
        raise MetadataSourceException('Error while querying RoMEO.\n'+
                'URL was: '+base_url+'\n'+
                'Parameters were: '+str(search_terms)+'\n'+
                'Error is: '+str(e))

    # Parse it
    try:
        parser = ET.XMLParser(encoding='utf-8')
        root = ET.parse(BytesIO(response), parser)
    except ET.ParseError as e:
        with open('/tmp/romeo_response.xml', 'w') as f:
            f.write(response)
            f.write('\n')
        raise MetadataSourceException('RoMEO returned an invalid XML response, dumped at /tmp/romeo_response.xml\n'+
                'URL was: '+base_url+'\n'+
                'Parameters were: '+str(search_terms)+'\n'+
                'Error is: '+str(e))

    return root


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


def fetch_journal(search_terms, matching_mode = 'exact'):
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
        search_terms[key] = remove_diacritics(search_terms[key])

    # First check we don't have it already
    journal = find_journal_in_model(search_terms)
    if journal:
        return journal

    # Perform the query
    root = perform_romeo_query(search_terms)

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

def fetch_publisher(publisher_name):
    print "Fetching publisher: "+publisher_name
    # First, let's see if we have a publisher with that name
    for p in Publisher.objects.filter(name=publisher_name)[:1]:
        print "Exact match"
        return p

    # Second, let's see if the publisher name has often been associated to a known publisher
    aliases = list(AliasPublisher.objects.filter(name=publisher_name).order_by('-count')[:2])
    if len(aliases) == 1:
        if aliases[0].count > PUBLISHER_NAME_ASSOCIATION_THRESHOLD:
            print "Found alias: "+unicode(aliases[0]).encode('utf-8')
            AliasPublisher.increment(publisher_name, aliases[0].publisher)
            return aliases[0].publisher
    elif len(aliases) == 2:
        if aliases[0].count > PUBLISHER_NAME_ASSOCIATION_FACTOR*aliases[1].count:
            print "Found alias: "+unicode(aliases[0]).encode('utf-8')
            print "Second result: "+unicode(aliases[1]).encode('utf-8')
            AliasPublisher.increment(publisher_name, aliases[0].publisher)
            return aliases[0].publisher
        else:
            print "Not clear enough:"
            print aliases[0]
            print aliases[1]
       

    # Otherwise, let's try to fetch the publisher from RoMEO!

    # Prepare the query
    search_terms = dict()
    search_terms['pub'] = remove_diacritics(publisher_name)
    search_terms['qtype'] = 'all'

    root = perform_romeo_query(search_terms)

    # Find the publisher
    publishers = root.findall('./publishers/publisher')
    if len(publishers) == 0:
        print "No results"
        return
    elif len(publishers) > 1:
        print str(len(publishers)) + " results"
        search_terms['qtype'] = 'exact'
        root = perform_romeo_query(search_terms)
        publishers = root.findall('./publishers/publisher')
        if len(publishers) != 1:
            print str(len(publishers)) + " results after exact"
            return

    print "Successfully fetched from RoMEO"
    publisher =  get_or_create_publisher(publishers[0])
    AliasPublisher.increment(publisher_name, publisher)
    return publisher

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

    # Update the publisher status
    publisher.oa_status = publisher.classify_oa_status()
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
        r = PublisherRestrictionDetail(publisher=publisher, applies_to=applies_to, text=text)
        r.save()

