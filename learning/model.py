# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import math
import cPickle

from papers.models import *
from papers.utils import iunaccent

def tokenize(l):
    return iunaccent(l).split()

class WordCount:
    def __init__(self):
        self.dirichlet = 1
        self.total = 0
        self.c = dict()
        self.stop = 0 # Unused
        self.mass = self.dirichlet
        self.cached = True

    def load(self, fname):
        f = open(f, 'rb')
        self = cPickle.load(f)
        f.close()

    def save(self, fname):
        f = open(f, 'wb')
        cPickle.save(f, self)
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
        total = 1
        for w in tokenize(l):
            total *= self.p(w)
        return total

    def lprobLine(self, l):
        total = 0
        for w in tokenize(l):
            total += self.lp(w)
        return total

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



