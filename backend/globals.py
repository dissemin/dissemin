# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from backend.similarity import *
from backend.relevance import *
from backend.clustering import *
from os.path import isfile

clustering_context_factory = None

if isfile('models/similarity.pkl'):
    print("Loading similarity classifier…")
    sc = SimilarityClassifier(filename='models/similarity.pkl')
    rc = OrcidRelevanceClassifier()

    clustering_context_factory = ClusteringContextFactory(sc, rc)
else:
    print('Not loading classifiers as they have not been trained.')


