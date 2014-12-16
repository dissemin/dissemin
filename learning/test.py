# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.models import *
from learning.model import *

w = WordCount()

for p in Paper.objects.filter(visibility="VISIBLE"):
    w.feedLine(p.title)

w.save('titles.wc')


