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

# Supported formats
#
# 'http://dx.doi.org/10.1145/1721837.1721839'
# '10.1145/1721837.1721839'
# 'DOI: 10.1145/1721837.1721839'
#
# These are all converted to
# '10.1145/1721837.1721839'
def to_doi(candidate):
    """ Convert a representation of a DOI to its normal form. """
    m = doi_re.match(candidate)
    if m:
        return m.groups()[0]
    else:
        return None

