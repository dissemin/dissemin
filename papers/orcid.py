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
from papers.name import normalize_name_words, parse_comma_name

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

def get_homepage_from_orcid_profile(profile):
    """
    Extract an URL for that researcher (if any)
    """
    lst = jpath('orcid-profile/orcid-bio/researcher-urls/researcher-url', profile)
    for url in lst:
        val = jpath('url/value', url)
        name = jpath('url-name/value', url).lower()
        if val and len(lst) == 1 or 'home' in name or 'personal' in name:
            return val
    if len(lst):
        return jpath('url/value', lst[0]) or None

def get_email_from_orcid_profile(profile):
    # TODO
    return None

def get_name_from_orcid_profile(profile):
    """
    Returns a parsed version of the "credit name" in the ORCID profile.
    If there is no such name, returns the given and family names on the profile
    (they should exist)
    """
    name_item = jpath('orcid-profile/orcid-bio/personal-details', profile)
    name = jpath('credit-name/value', name_item)
    if name is not None:
        return parse_comma_name(name)
    return (normalize_name_words(jpath('given-names/value', name_item)),
            normalize_name_words(jpath('family-name/value', name_item)))

def get_other_names_from_orcid_profile(profile):
    """
    Returns the list of other names listed on the ORCiD profile.
    This includes the (given,family) name if a credit name was defined.
    """
    name_item = jpath('orcid-profile/orcid-bio/personal-details', profile)
    names = []
    credit_name = jpath('credit-name/value', name_item)
    if credit_name is not None:
        print "Found credit name "+unicode(credit_name)
        names.append((normalize_name_words(jpath('given-names/value', name_item)),
            normalize_name_words(jpath('family-name/value', name_item))))
    other_names = jpath('other-names/other-name', name_item, default=[])
    for name in other_names:
        val = name.get('value')
        if val is not None:
            names.append(parse_comma_name(val))
    print(names)
    return names



