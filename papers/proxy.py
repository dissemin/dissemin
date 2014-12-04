# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader

from papers.oai import my_oai_dc_reader

# A few settings telling how to access the OAI proxy
PROXY_ENDPOINT = "http://proaixy.dissem.in/oai"

PROXY_DAY_GRANULARITY = False

PROXY_SOURCE_PREFIX = "proaixy:source:"
PROXY_AUTHOR_PREFIX = "proaixy:author:"

def get_proxy_client():
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', my_oai_dc_reader)
    client = Client(PROXY_ENDPOINT, registry)
    client._day_granularity = PROXY_DAY_GRANULARITY
    return client


