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

from oaipmh.metadata import MetadataReader

base_dc_reader = MetadataReader(
    fields={
    'title':       ('textList', 'base_dc:dc/dc:title/text()'),
    'creator':     ('textList', 'base_dc:dc/dc:creator/text()'),
    'subject':     ('textList', 'base_dc:dc/dc:subject/text()'),
    'description': ('textList', 'base_dc:dc/dc:description/text()'),
    'publisher':   ('textList', 'base_dc:dc/dc:publisher/text()'),
    'contributor': ('textList', 'base_dc:dc/dc:contributor/text()'),
    'date':        ('textList', 'base_dc:dc/dc:date/text()'),
    'type':        ('textList', 'base_dc:dc/dc:type/text()'),
    'format':      ('textList', 'base_dc:dc/dc:format/text()'),
    'identifier':  ('textList', 'base_dc:dc/dc:identifier/text()'),
    'source':      ('textList', 'base_dc:dc/dc:source/text()'),
    'language':    ('textList', 'base_dc:dc/dc:language/text()'),
    'relation':    ('textList', 'base_dc:dc/dc:relation/text()'),
    'rights':      ('textList', 'base_dc:dc/dc:rights/text()'),
    'autoclasscode':('textList', 'base_dc:dc/base_dc:autoclasscode/text()'),
    'classcode':('textList', 'base_dc:dc/base_dc:classcode/text()'),
    'collection':('textList', 'base_dc:dc/base_dc:collection/text()'),
    'collname':('textList', 'base_dc:dc/base_dc:collname/text()'),
    'continent':('textList', 'base_dc:dc/base_dc:continent/text()'),
    'country':('textList', 'base_dc:dc/base_dc:country/text()'),
    'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
    'lang':('textList', 'base_dc:dc/base_dc:lang/text()'),
    'link':('textList', 'base_dc:dc/base_dc:link/text()'),
    'oa':('textList', 'base_dc:dc/base_dc:oa/text()'),
    'rightsnorm':('textList', 'base_dc:dc/base_dc:rightsnorm/text()'),
    'typenorm':('textList', 'base_dc:dc/base_dc:typenorm/text()'),
    'year':('textList', 'base_dc:dc/base_dc:year/text()'),
    },
    namespaces={
    'base_dc': 'http://oai.base-search.net/base_dc/',
    'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc' : 'http://purl.org/dc/elements/1.1/'}
    )

