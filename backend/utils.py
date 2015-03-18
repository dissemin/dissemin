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

import requests
import requests.exceptions
from time import sleep
from titlecase import titlecase

from papers.errors import MetadataSourceException

### Open an URL with retries

def urlopen_retry(url, **kwargs):# data, timeout, retries, delay, backoff):
    data = kwargs.get('data', None)
    timeout = kwargs.get('timeout', 10)
    retries = kwargs.get('retries', 3)
    delay = kwargs.get('delay', 5)
    backoff = kwargs.get('backoff', 2)
    headers = kwargs.get('headers', {})
    try:
        r = requests.get(url,
                params=data,
                timeout=timeout,
                headers=headers,
                allow_redirects=True)
        return r.text
    except requests.exceptions.Timeout as e:
        if retries <= 0:
            raise MetadataSourceException('Timeout: '+str(e))
    except requests.exceptions.ConnectionError as e:
        if retries <= 0:
            raise MetadataSourceException('Connection error: '+str(e))
    except requests.exceptions.RequestException as e:
        raise MetadataSourceException('Request error: '+str(e))

    print "Retrying in "+str(delay)+" seconds..."
    print "URL: "+url
    sleep(delay)
    return urlopen_retry(url,
            data=data,
            timeout=timeout,
            retries=retries-1,
            delay=delay*backoff,
            backoff=backoff)

# Recapitalize a title if it is mostly uppercase
def maybe_recapitalize_title(title):
    nb_upper = 0
    nb_lower = 0
    for i in range(len(title)):
        if title[i].isupper():
            nb_upper += 1
        elif title[i].islower():
            nb_lower += 1

    if nb_upper > nb_lower:
        title = titlecase(title)
    return title

