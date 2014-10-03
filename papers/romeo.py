# -*- encoding: utf-8 -*-
from urllib2 import urlopen, HTTPError, URLError
from papers.models import *
from papers.errors import MetadataSourceException
import xml.etree.ElementTree as ET

api_key = open('romeo_api_key').read().strip()

def fetch_journal(search_terms):
    """
    Fetch the journal data from RoMEO. Returns an Journal object.
    search_terms should be a dictionnary object containing at least one of these fields:
    """
    allowed_fields = ['issn', 'jtitle']


    # Check the arguments
    if not all(lambda x: x in allowed_fields, key for key in search_terms):
        raise ValueError('The search terms have to belong to '+str(allowed_fields)+
                'but the dictionary I got is '+str(search_terms))

    # Prepare the query
    if api_key:
        search_terms['ak'] = api_key
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
    journals = root.iter('journal')
    if not journals:
        return None
    if len(journals) > 1:
        print ("Warning, "+str(len(journals))+" journals match the RoMEO request, "+
                "defaulting to the first one")
    journal = journals[0]

    names = journal.filter('jtitle')
    if not names:
        raise MetadataSourceException('RoMEO returned a journal without title.\n'+
                'URL was: '+request)
    if len(names) > 1:
        print("Warning, "+str(len(names))+" names provided for one journal, "+
                "defaulting to the first one")
    name = names[0].text
    
    issn = None
    try:
        issn = journal.filter('issn')[0].text
    except KeyError, IndexError:
        pass

    publishers = journal.filter('publisher')
    if not publishers:
        raise MetadataSourceException('RoMEO provided a journal but no publisher.\n'+
                'URL was: '+request)
    # TODO here we shouldn't default to the first one but look it up using the <romeopub>
    publisher_desc = publishers[0]

    publisher = get_or_create_publisher(publisher_desc)

    # TODO lookup first to see if it already exists
    result = Journal(title=name,issn=issn,publisher=publisher)
    result.save()
    return result

def get_or_create_publisher(romeo_xml_description):
    """
    Retrieves from the model, or creates into the model,
    the publisher corresponding to the <publisher> description
    from RoMEO
    """
    # TODO TODO TODO
    return 

