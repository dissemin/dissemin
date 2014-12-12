# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from papers.errors import MetadataSourceException
from papers.backend import *

from urllib2 import urlopen, URLError
from urllib import urlencode
import xml.etree.ElementTree as ET
import unicodedata

bielefeld_timeout = 10

def fetch_papers_from_base_by_researcher_name(name):
    base_url = 'http://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi'
    base_source, created = OaiSource.objects.get_or_create(identifier='base',name='BASE')
    
    search_terms = name[0]+' '+name[1]
    try:
        offset = 0
        nb_results = 1
        while offset < nb_results:
            query_args = {'func':'PerformSearch',
                    'offset':str(offset),
                    'query':search_terms}
            request = base_url+'?'+urlencode(query_args)
            f = urlopen(request)
            response = f.read()
            root = ET.fromstring(response)
            result_list = list(root.findall('./result'))
            if not result_list:
                raise MetadataSourceException('BASE returned no results for URL '+request)
            result_list = result_list[0]
            try:
                nb_results = int(result_list.attrib['numFound'])
            except (KeyError, IndexError, ValueError):
                raise MetadataSourceException('Invalid number of results in BASE response, '+request)
            doc_list = list(result_list.findall('./doc'))
            if not doc_list:
                break
            offset += len(doc_list)

            for doc in doc_list:
                try:
                    add_base_document(doc, base_source)
                except MetadataSourceException as e:
                    raise MetadataSourceException(str(e)+'\nIn URL: '+request)

    except URLError as e:
        raise MetadataSourceException('Error while fetching metadata from BASE:\n'+
                'Unable to open the URL: '+request+'\n'+
                'Error was: '+str(e))
    except ET.ParseError as e:
        raise MetadataSourceException('Error while fetching metadata from BASE:\n'+
                'The XML document returned by the following URL is invalid:\n'+
                request+'\n'+
                'Reason: '+str(e))

def base_xml_to_dict(doc):
    dct = dict()
    strings = doc.findall('./str')
    for s in strings:
        if 'name' in s.attrib:
            dct[s.attrib['name']] = s.text
    arrays = doc.findall('./arr')
    for a in arrays:
        if 'name' in a.attrib:
            lst = []
            for s in a.findall('./str'):
                lst.append(s.text)
            dct[a.attrib['name']] = lst
    return dct

def add_base_document(doc, source):
    metadata = base_xml_to_dict(doc)
    if not 'dctitle' in metadata:
        return
    title = metadata['dctitle']
    if not 'dccreator' in metadata:
        return
    creators = metadata['dccreator']
    if type(creators) == type(''):
        creators = [creators]
    author_names = map(parse_comma_name, creators)
    
    try:
        year = int(metadata['dcyear'])
    except ValueError as e:
        raise MetadataSourceException('BASE returned an invalid year for the document "'+
            title+'" : "'+metadata['dcyear']+'"')
    except KeyError: # No dcyear attribute, let's try to extract it from the date
        try:
            date = metadata['dcdate']
            year_re = re.compile(r'[12][0-9][0-9][0-9]')
            match = year_re.search(date)
            if match:
                year = int(match.group(0))
            else:
                raise ValueError
        except (KeyError,ValueError): # No dcdate either
            print("Warning, skipping document because no year or date is provided\n"+
                'In document "'+title+'"')
            return False
    
    # Lookup the names and check that at least one of them is known
    model_names = []
    researcher_found = False
    for name in author_names:
        mn = lookup_name(name)
        model_names.append(mn)
        if mn.researcher:
            researcher_found = True

    if not researcher_found:
        return False

    if not 'dcdocid' in metadata:
        print("Warning, skipping BASE record because no DOCID is provided\n"+
                "In document '"+title+"'")
        return False

    identifier = 'base:'+metadata['dcdocid']
    doi = None
    description = metadata.get('dcdescription')
    splash_url = metadata.get('dclink')
    pdf_url = None
    if splash_url and splash_url.endswith('.pdf'):
        pdf_url = splash_url
    for url in metadata.get('dcidentifier', []):
        if url.endswith('.pdf'):
            pdf_url = url
    if metadata.get('dcsource', '').endswith('.pdf'):
        pdf_url = metadata['dcsource']

    if not (pdf_url or splash_url):
        return False

    paper = get_or_create_paper(title, model_names, year, doi, 'CANDIDATE')
    
    record = OaiRecord(
            source=source,
            identifier=identifier,
            splash_url=splash_url,
            pdf_url=pdf_url,
            about=paper,
            description=description)
    record.save()

    paper.update_pdf_url()
    return True




