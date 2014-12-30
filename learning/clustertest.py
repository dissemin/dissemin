from papers.clustering import *
from papers.models import *
from django.db.models import Q
rpk=1208
npk=Researcher.objects.get(pk=rpk).name.pk

authors = Author.objects.filter(name_id=npk).filter(
        Q(paper__visibility='VISIBLE') | Q(paper__visibility='DELETED')).order_by('id')

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



sc = SimilarityClassifier(filename='models/similarity.pkl')
print(sc.confusion(features, labels))

cc = ClusteringContext(authors, sc)

logf = open('log-clustering', 'w')

count = len(authors)
idx = 0
for a in authors:
    print "# "+str(idx)+"/"+str(count)+" ## "+str(a.paper)
    cc.runClustering(a.pk, True, logf)
    idx += 1

logf.close()

