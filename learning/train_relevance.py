# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.db.models import Q
from papers.models import *
from learning.model import *
from papers.relevance import *

# Read dataset
author_ids = []
labels = []
for line in open('learning/dataset/relevance_training_ids', 'r'):
    vals = map(lambda x: int(x), line.strip().split('\t'))
    author_ids.append((vals[0], vals[1]))
    labels.append(vals[2])

rc = RelevanceClassifier()

make_lm = True
if make_lm:
    print("Language model")
    i = 0
    for author in Author.objects.filter(name__researcher__department_id=21,paper__visibility='VISIBLE'):
        if i % 100 == 0:
            print(i)
        rc.feed(author, 21)
        i += 1
    rc.save('models/relevance.pkl')
else:
    rc.load('models/relevance.pkl')

recompute = True
if recompute:
    print("Computing features")
    features = []
    for (id,dpt) in author_ids:
        author = Author.objects.get(pk=id)
        f = rc.computeFeatures(author, dpt)
        features.append(f)
    print("Writing features back")
    outf = open('learning/dataset/relevance-features', 'w')
    for i in range(len(features)):
        print('\t'.join(map(lambda x: str(x), features[i])), file=outf)
    outf.close()
else:
    inf = open('learning/dataset/relevance-features', 'r')
    features = []
    for line in inf:
        f = map(lambda x: float(x), line.strip().split('\t'))
        features.append(f)
    inf.close()


rc.train(features, labels, 'linear')
print(rc.confusion(features, labels))
rc.save('models/relevance.pkl')



