# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from backend.similarity import *
from backend.relevance import *
from backend.clustering import *


print("Loading similarity classifier…")
sc = SimilarityClassifier(filename='models/similarity.pkl')
relevance_stage = 0
if relevance_stage == 0:
    print('Loading dummy relevance classifier…')
    rc = DummyRelevanceClassifier()
else:
    print("Loading relevance classifier…")
    rc = RelevanceClassifier(filename='models/relevance-'+str(relevance_stage)+'.pkl')

clustering_context_factory = ClusteringContextFactory(sc, rc)


