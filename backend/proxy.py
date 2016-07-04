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

# A few settings telling how to access the OAI proxies

# This one is for the repositories we harvest manually
# These papers will be included in the search results
# even if they are not present in any other source
PROXY_ENDPOINT = "http://proaixy.dissem.in/oai"

# This one is for results from BASE
# It is only used to fetch availability of existing papers
# (we do not search by author name in this repository)
BASE_LOCAL_ENDPOINT = "http://doai.dissem.in/oai"

PROXY_DAY_GRANULARITY = False

PROXY_SOURCE_PREFIX = "proaixy:source:"
PROXY_AUTHOR_PREFIX = "proaixy:author:"
PROXY_SIGNATURE_PREFIX = "proaixy:authorsig:"
PROXY_FINGERPRINT_PREFIX = "proaixy:fingerprint:"
PROXY_DOI_PREFIX = "proaixy:doi:"

import json
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, MetadataReader
from oaipmh import common
from oaipmh.metadata import oai_dc_reader, base_dc_reader

class CiteprocReader(MetadataReader):
    def __init__(self):
        super(CiteprocReader, self).__init__({},{})

    def __call__(self, element):
        # extract the Json
        jsontxt = element.text
        payload = json.loads(jsontxt)

        return common.Metadata(element, payload)

citeproc_reader = CiteprocReader()

# Reader slightly tweaked because Cairn includes a useful non-standard field
my_oai_dc_reader = oai_dc_reader
my_oai_dc_reader._fields['accessRights'] = ('textList', 'oai_dc:dc/dcterms:accessRights/text()')
my_oai_dc_reader._namespaces['dcterms'] = 'http://purl.org/dc/terms/'


def get_proxy_client():
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', my_oai_dc_reader)
    client = Client(PROXY_ENDPOINT, registry)
    client._day_granularity = PROXY_DAY_GRANULARITY
    return client

def get_base_client():
    registry = MetadataRegistry()
    registry.registerReader('base_dc', base_dc_reader)
    client = Client(BASE_LOCAL_ENDPOINT, registry)
    return client

