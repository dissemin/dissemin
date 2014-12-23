# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


from __future__ import unicode_literals

import math
import cPickle

from papers.models import *
from papers.utils import iunaccent
from nltk.tokenize.punkt import PunktWordTokenizer

punktTokenizer = PunktWordTokenizer()

def tokenize(l):
    return punktTokenizer.tokenize(iunaccent(l))

class WordCount:
    def __init__(self):
        self.dirichlet = 1.
        self.total = 0
        self.c = dict()
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
        count = self.c.get(w,0)
        return (count + self.dirichlet) / self.mass

    def lp(self, w):
        if not self.cached:
            self._cache()
        count = self.c.get(w,0)
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

    def lProbLine(self, l):
        total = 0.
        for w in tokenize(l):
            total += self.lp(w)
        return total

    def nlProbLine(self, l):
        total = 0.
        lgt = 0
        for w in tokenize(l):
            total += self.lp(w)
            lgt += 1
        return total / lgt

    def _countWord(self, w):
        c = self.c.get(w,0)
        self.c[w] = c+1
        self.total += 1
        self.cached = False

    def _cache(self):
        self.mass = ((len(self.c) + 1)*self.dirichlet + self.total)


class DepartmentModel:
    def __init__(self):
        self.wc_title = WordCount()



