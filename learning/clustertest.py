from papers.clustering import *
from papers.models import *
from django.db.models import Q
npk=13381
authors = Author.objects.filter(name_id=npk).filter(
        Q(paper__visibility='VISIBLE') | Q(paper__visibility='DELETED')).order_by('id')

# Cleaning
for a in authors:
    a.cluster = None
    a.num_children = 1
    a.save(update_fields=['cluster','num_children'])

count = len(authors)
idx = 0
for a in authors:
    print "# "+str(idx)+"/"+str(count)+" ## "+str(a.paper)
    runClustering(a)
    idx += 1


