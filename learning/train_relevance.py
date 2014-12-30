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

all_fields_model = WordCount()
all_fields_model.load('models/everything.pkl')
contributors_model = WordCount()
contributors_model.load('models/contributors.pkl')
rc = RelevanceClassifier(languageModel=all_fields_model,contributorsModel=contributors_model)

make_lm = False
if make_lm:
    print("Topic model")
    i = 0
    for author in Author.objects.filter(name__researcher__department_id=21,paper__visibility='VISIBLE'):
        if i % 100 == 0:
            print(i)
        rc.feed(author, 21)
        i += 1
    rc.save('models/relevance.pkl')
else:
    rc.load('models/relevance.pkl')

recompute = False
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

def paper_url(pk):
    print('http://localhost:8000/paper/'+str(Author.objects.get(pk=pk).paper_id))

for i in range(len(labels)):
    prediction = rc.classifier.predict(features[i])[0]
    if labels[i] == 0 and prediction == 1:
        print("#####")
        paper_url(author_ids[i][0])
        print("Explanation")
        print(rc.computeFeatures(Author.objects.get(pk=author_ids[i][0]), 21, explain=True))


print(rc.confusion(features, labels))
rc.save('models/relevance.pkl')



