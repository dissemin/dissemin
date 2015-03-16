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

from papers.models import Name
from collections import defaultdict

class NameCache(object):
    """
    Simple cache to save name lookups
    """
    def __init__(self):
        self.dct = dict()
        self.cnt = defaultdict(int)

    def lookup(self, name):
        self.cnt[name] += 1
        if name in self.dct:
            return self.dct[name]

        val = Name.lookup_name(name)
        self.dct[name] = val
        return val

    def prune(self, threshold):
        for k in self.cnt:
            if self.cnt[k] <= threshold:
                del self.cnt[k]
                del self.dct[k]
 

name_lookup_cache = NameCache()


