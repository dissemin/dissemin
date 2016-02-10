# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals
import re

# DOIs have very few limitations on what can appear in them
# see the standards
# hence a quite permissive regexp, as we use it in a controlled
# environment: fields of a metadata record and not plain text

doi_re = re.compile(r'^ *(?:[Dd][Oo][Ii] *[:=])? *(?:http://dx\.doi\.org/)?(10\.[0-9]{4,}[^ ]*/[^ ]+) *$')
openaire_doi_re = re.compile(r'info:eu-repo/semantics/altIdentifier/doi/(10\.[0-9]{4,}[^ ]*/[^ ]+) *') 

def to_doi(candidate):
    """
    >>> to_doi('http://dx.doi.org/10.1145/1721837.1721839')
    u'10.1145/1721837.1721839'
    >>> to_doi('10.1145/1721837.1721839')
    u'10.1145/1721837.1721839'
    >>> to_doi('DOI: 10.1145/1721837.1721839')
    u'10.1145/1721837.1721839'
    >>> to_doi('info:eu-repo/semantics/altIdentifier/doi/10.1145/1721837.1721839')
    u'10.1145/1721837.1721839'
    >>> to_doi('10.1093/jhmas/XXXI.4.480')
    u'10.1093/jhmas/xxxi.4.480'
    """
    m = doi_re.match(candidate)
    if m:
        return m.groups()[0].lower()
    else:
        openaire_match = openaire_doi_re.match(candidate)
        if openaire_match:
            return openaire_match.group(1).lower()

