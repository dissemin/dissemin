# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.clustering import *

print("Loading similarity classifier…")
sc = SimilarityClassifier(filename='models/similarity.pkl')
print("Loading relevance classifier…")
rc = RelevanceClassifier(filename='models/relevance.pkl')

def cluster(rpk):
    return clusterResearcher(rpk, sc, rc)

