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

import requests, json
from papers.errors import MetadataSourceException
from papers.name import normalize_name_words

def jpath(path, js, default=None):
    def _walk(lst, js):
        if js is None:
            return default
        if lst == []:
            return js
        else:
            return _walk(lst[1:], js.get(lst[0],{} if len(lst) > 1 else default))
    return _walk(path.split('/'), js)

def get_orcid_profile(id):
    try:
        headers = {'Accept':'application/orcid+json'}
        profile_req = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % id, headers=headers)
        return profile_req.json()
    except requests.exceptions.HTTPError:
        raise MetadataSourceException('The ORCiD %s could not be found' % id)
    except (ValueError, TypeError) as e:
        raise MetadataSourceException('The ORCiD %s returned invalid JSON.' % id)


def get_name_from_orcid_profile(profile):
    name_item = jpath('orcid-profile/orcid-bio/personal-details', profile)
    return (normalize_name_words(jpath('given-names/value', name_item)),
            normalize_name_words(jpath('family-name/value', name_item)))


