# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


from __future__ import unicode_literals

import math
import cPickle
from collections import defaultdict

from papers.models import *
from papers.utils import iunaccent, tokenize

class WordCount:
    def __init__(self):
        self.dirichlet = 1.
        self.total = 0
        self.c = defaultdict(int)
        self.stop = 0 # Unused
        self.mass = self.dirichlet
        self.cached = True

    def load(self, fname):
        f = open(fname, 'rb')
        dct = cPickle.load(f)
        f.close()
        self.__dict__.update(dct)

    def save(self, fname):
        f = open(fname, 'wb')
        cPickle.dump(self.__dict__, f)
        f.close()
    
    def p(self, w):
        if not self.cached:
            self._cache()
        count = self.c[w]
        return (count + self.dirichlet) / self.mass

    def lp(self, w):
        if not self.cached:
            self._cache()
        count = self.c[w]
        return math.log(count + self.dirichlet) - math.log(self.mass)

    def feedLine(self, l):
        for w in tokenize(l):
            self._countWord(w)
        # self.stop += 1
        # self.total += 1

    def probLine(self, l):
        total = 1.
        for w in tokenize(l):
            total *= self.p(w)
        return total

    def lProbLine(self, l, threshold=None):
        total = 0.
        for w in tokenize(l):
            lp = self.lp(w)
            if threshold == None or lp >= -threshold:
                total += lp
        return total

    def nlProbLine(self, l):
        total = 0.
        lgt = 0
        for w in tokenize(l):
            total += self.lp(w)
            lgt += 1
        if lgt > 0:
            return total / lgt
        return 0.

    def _countWord(self, w):
        self.c[w] += 1
        self.total += 1
        self.cached = False

    def _cache(self):
        self.mass = ((len(self.c) + 1)*self.dirichlet + self.total)


class DepartmentModel:
    def __init__(self):
        self.wc_title = WordCount()



