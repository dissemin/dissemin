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

"""
This module caches name lookups in memory.
This is especially useful when fetching new papers,
as we have to look up every author name, checking
whether we have already a model instance for it.
"""

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
        """
        :param name: a `(first,last)` pair representing a name.
        :returns: a :class:`.Name` instance, which is not saved (has no `id`)
            if the name is new.
        """
        if name in self.dct:
            self.cnt[name] += 1
            return self.dct[name]

        val = Name.lookup_name(name)
        if val.pk is not None:
            self.dct[name] = val
            self.cnt[name] += 1
        return val

    def prune(self, threshold=None):
        """
        Prunes all the instances that have been looked up less than
        `threshold` times.
        :param threshold: mininum number of lookups for a :class:`.Name` to be kept.
            If `None`, clears all the names.
        """
        if threshold is None:
            self.cnt.clear()
            self.dct.clear()
            return
        for k in self.cnt.keys():
            if self.cnt[k] <= threshold:
                del self.cnt[k]
                del self.dct[k]
 
    def check(self):
        """
        Perform a sanity check of the cache (used in tests)
        :returns: `True` when the cache is sane.
        """
        if set(self.dct.keys()) != set(self.cnt.keys()):
            return False
        if not all(map(lambda (k,v): v > 0, self.cnt.items())):
            return False
        return True

#: Global name lookup cache, mostly used by the tasks backend.
name_lookup_cache = NameCache()


