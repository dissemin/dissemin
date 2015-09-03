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

# A few settings telling how to access the OAI proxy
PROXY_ENDPOINT = "http://proaixy.dissem.in/oai"

PROXY_DAY_GRANULARITY = False

PROXY_SOURCE_PREFIX = "proaixy:source:"
PROXY_AUTHOR_PREFIX = "proaixy:author:"
PROXY_SIGNATURE_PREFIX = "proaixy:authorsig:"
PROXY_FINGERPRINT_PREFIX = "proaixy:fingerprint:"


from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry, oai_dc_reader
from backend.oai import my_oai_dc_reader

def get_proxy_client():
    registry = MetadataRegistry()
    registry.registerReader('oai_dc', my_oai_dc_reader)
    client = Client(PROXY_ENDPOINT, registry)
    client._day_granularity = PROXY_DAY_GRANULARITY
    return client


