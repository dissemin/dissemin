# -*- coding: utf-8 -*-

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

from papers.errors import MetadataSourceException
from papers.backend import *
from papers.utils import iunaccent

from urllib2 import urlopen, URLError
from urllib import urlencode
import xml.etree.ElementTree as ET
import unicodedata

bielefeld_timeout = 10
max_base_no_match = 30

def fetch_papers_from_base_for_researcher(researcher):
    for name in researcher.name_set.all():
        fetch_papers_from_base_by_researcher_name((name.first,name.last))

def fetch_papers_from_base_by_researcher_name(name):
    base_url = 'http://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi'
    base_source, created = OaiSource.objects.get_or_create(identifier='base',name='BASE',priority=0)
    
    search_terms = iunaccent(name[0]+' '+name[1])
    try:
        offset = 0
        nb_results = 1
        no_match = 0
        while offset < nb_results and no_match < max_base_no_match:
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
                    if add_base_document(doc, base_source):
                        no_match = 0
                    else:
                        no_match += 1
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
    
    # TODO: this would be more flexible (but should be done for OAI and CrossRef as well -> refactor)
    # researcher_found = False
    # for author in author_names:
    #    count = Name.objects.filter(last__iexact=author[1],is_known=True).count()
    #    if count > 0:
    #        researcher_found = True
    #        break
    #if not researcher_found:
    #    return False

    # Lookup the names
    model_names = map(lookup_name, author_names)

    # Check that at least one of the last names is known
    # TODO remove this and do the things above
    if all(not elem.is_known for elem in model_names):
        return False

    if not 'dcdocid' in metadata:
        print("Warning, skipping BASE record because no DOCID is provided\n"+
                "In document '"+title+"'")
        return False
    identifier = 'base:'+metadata['dcdocid']
    if OaiRecord.objects.filter(identifier=identifier).first():
        return True

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
            description=description,
            priority=source.priority)
    record.save()

    paper.update_pdf_url()
    return True




