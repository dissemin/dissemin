# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.clustering import *
from papers.globals import *
from papers.models import *

def cluster(rpk):
    researcher = Researcher.objects.get(pk=rpk)
    clustering_context_factory.load(researcher)
    clustering_context_factory.reclusterBatch(researcher)

