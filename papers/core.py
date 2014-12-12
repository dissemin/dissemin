# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone

from papers.errors import MetadataSourceException
from papers.backend import *
from papers.models import *
from papers.oai import my_oai_dc_reader
from papers.name import parse_comma_name

from urllib2 import urlopen, URLError
from urllib import urlencode, quote_plus
from lxml import etree
import unicodedata

core_timeout = 10
max_no_match_before_give_up = 25
core_api_key = open('core_api_key').read().strip()

def fetch_papers_from_core_by_researcher_name(name):
    base_url = 'http://core.kmi.open.ac.uk/api/search/'
    core_source = OaiSource.objects.get_or_create(identifier='core',
            name='CORE',
            url_extractor='core',
            defaults={'last_update': timezone.now()})
    
    search_terms = 'author:'+quote_plus('('+name[0]+' '+name[1]+')')
    try:
        offset = 0
        nb_results = 1
        no_match = 0
        while offset < nb_results and no_match < max_no_match_before_give_up:
            query_args = {'api_key':core_api_key,
                    'offset':str(offset)}
            request = base_url+search_terms+'?'+urlencode(query_args)
            f = urlopen(request)
            response = f.read()
            root = etree.fromstring(response)
            result_list = list(root.iter('record'))
            if not result_list:
                raise MetadataSourceException('CORE returned no results for URL '+request)

            try:
                nb_results = int(list(root.iter('total_hits'))[0].text)
            except (KeyError, IndexError, ValueError):
                raise MetadataSourceException('Invalid number of results in CORE response, '+request)

            offset += len(result_list)

            for doc in result_list:
                try:
                    match = add_core_document(doc, core_source)
                    if match:
                        no_match = 0
                    else:
                        no_match += 1
                except MetadataSourceException as e:
                    raise MetadataSourceException(str(e)+'\nIn URL: '+request)
    except URLError as e:
        raise MetadataSourceException('Error while fetching metadata from CORE:\n'+
                'Unable to open the URL: '+request+'\n'+
                'Error was: '+str(e))
    except etree.ParseError as e:
        raise MetadataSourceException('Error while fetching metadata from CORE:\n'+
                'The XML document returned by the following URL is invalid:\n'+
                request+'\n'+
                'Reason: '+str(e))

core_sep_re = re.compile(r', *| *and *')
def parse_core_authors_list(lst):
    return core_sep_re.split(lst)

def add_core_document(doc, source):
    xml_record = list(doc.iter('metadata'))[0]
    metadata = my_oai_dc_reader(xml_record)._map
    authors_list = metadata.get('creator', [])
    if not authors_list:
        print "Ignoring CORE record as it has no creators."
        return False
    authors_list = parse_core_authors_list(authors_list[0])
    authors_list = map(parse_comma_name, authors_list)
    authors = map(lookup_name, authors_list)
    
    # Filter the record
    if all(not elem.is_known for elem in authors):
        return False
    if not 'title' in metadata or metadata['title'] == []:
        return False
    print metadata['title']
    print authors_list
    return True



