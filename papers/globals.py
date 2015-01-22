# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from papers.similarity import *
from papers.relevance import *
from papers.clustering import *


print("Loading similarity classifier…")
sc = SimilarityClassifier(filename='models/similarity.pkl')
print("Loading relevance classifier…")
rc = RelevanceClassifier(filename='models/relevance-1.pkl')

clustering_context_factory = ClusteringContextFactory(sc, rc)


