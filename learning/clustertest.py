# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.clustering import *
from papers.relevance import *
from papers.models import *
from django.db.models import Q
researcher=Researcher.objects.get(pk=1024)
npk=researcher.name.pk

authors = Author.objects.filter(name_id=npk).filter(
        Q(paper__visibility='VISIBLE') | Q(paper__visibility='DELETED')).order_by('id')

# Delete researchers
authors.update(researcher=None,cluster=None)

print("Loading similarity classifier…")
sc = SimilarityClassifier(filename='models/similarity.pkl')
print("Loading relevance classifier…")
rc = RelevanceClassifier(filename='models/relevance.pkl')

if False:
    inf = open('learning/dataset/author-features', 'r')
    features = []
    for line in inf:
        f = map(lambda x: float(x), line.strip().split('\t'))
        features.append(f)
    inf.close()

    # Read dataset
    author_ids = []
    labels = []
    for line in open('learning/dataset/author_ids', 'r'):
        vals = map(lambda x: int(x), line.strip().split('\t'))
        author_ids.append((vals[0],vals[1]))
        labels.append(vals[2])

    print(sc.confusion(features, labels))


cc = ClusteringContext(authors, sc, rc)

logf = open('log-clustering', 'w')

print("Fetching authors…")
authors = list(authors)
count = len(authors)
idx = 0
for a in authors:
    print "# "+str(idx)+"/"+str(count)+" ## "+unicode(a.paper)
    cc.runClustering(a.pk, researcher, True, logf)
    idx += 1

cc.commit()
logf.close()

graphf = open('learning/gephi/classified-'+str(researcher.pk)+'.gdf', 'w')
cc.outputGraph(graphf)
graphf.close()


