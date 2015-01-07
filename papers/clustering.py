# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function

from papers.similarity import SimilarityClassifier
from papers.relevance import RelevanceClassifier
from papers.models import Author, Researcher
from django.db.models import Q
import random

# For graph output
from papers.utils import nocomma
from unidecode import unidecode

def clusterResearcher(rpk, sc, rc):
    researcher=Researcher.objects.get(pk=rpk)
    npk=researcher.name.pk

    authors = Author.objects.filter(name_id=npk).filter(
            Q(paper__visibility='VISIBLE') | Q(paper__visibility='DELETED')).order_by('id')

    # Delete researchers
    print("Removing previous clustering output…")
    authors.update(researcher=None,cluster=None,num_children=1)

    cc = ClusteringContext(authors, researcher, sc, rc)

    logf = open('log-clustering', 'w')

    print("Fetching authors…")
    authors = list(authors)
    count = len(authors)
    idx = 0
    for a in authors:
        print("# "+str(idx)+"/"+str(count)+" ## "+unicode(a.paper_id))
        cc.runClustering(a.pk, True, logf)
        idx += 1
    logf.close()

    cc.commit()

    graphf = open('learning/gephi/classified-'+str(researcher.pk)+'.gdf', 'w')
    cc.outputGraph(graphf)
    graphf.close()
    return cc


class ClusteringContext(object):
    def __init__(self, author_queryset, researcher, sc, rc):
        """
        Caveat: the author_queryset has to be closed under the "children" relation.
        """
        # All these dicts have PKs as keys
        # The django Author objects
        self.authors = dict()
        # The pk of the parent (if any)
        self.parent = dict()
        # The pk of the author that was found similar when merging two clusters (if any)
        # TODO this does not make any sense
        self.similar = dict()
        # The pks of the children (in the union find)
        self.children = dict()
        # The number of indirect children
        self.cluster_size = dict()
        # The number of indirect children classified as relevant for the researcher
        self.num_relevant = dict()
        # The id of the roots of the clusters
        self.cluster_ids = set()
        # Has this paper been tested for relevance yet?
        self.relevance_computed = dict()
        # For debugging purposes only
        self.relevance = dict()

        # Researcher we're trying to cluster
        self.researcher = researcher

        # The similarity and relevance classifiers
        self.sc = sc
        self.rc = rc

        # The author data used for the similarity classifier (cached)
        self.author_data = dict()

        for author in author_queryset:
            pk = author.pk
            self.authors[pk] = author
            if pk != author.cluster_id:
                self.parent[pk] = author.cluster_id
            self.similar[pk] = author.similar
            self.children[pk] = [child.pk for child in author.clusterrel.all()]
            if author.cluster_id == None:
                self.cluster_ids.add(pk)
            self.author_data[pk] = sc.getDataById(pk)
            self.num_relevant[pk] = 0
            self.cluster_size[pk] = author.num_children

    def commit(self):
        for (pk,val) in self.authors.items():
            val.cluster_id = self.find(pk)
            val.similar_id = self.similar.get(pk,None)
            val.num_children = self.cluster_size[pk]
            cluster_size = self.cluster_size[val.cluster_id]
            if self.num_relevant[val.cluster_id] >= cluster_size/2.0:
                val.researcher_id = self.researcher.id
            else:
                val.researcher_id = None
            # Num_relevant is not stored as it is department-centric
            # whereas the clusters themselves are "universal"
            val.save()

    def classify(self, pkA, pkB):
        # No need to cache as the algorithm already performs every test
        # at most once
        return self.sc.classifyData(self.author_data[pkA], self.author_data[pkB])

    def sample_with_multiplicity(self, nb_samples, root_idx):
        population_size = self.cluster_size[root_idx]
        if nb_samples < population_size:
            nb_samples = min(nb_samples, population_size)
            indices = random.sample(xrange(population_size), nb_samples)
            indices.sort()
        else:
            indices = range(population_size)

        return self.do_sample_with_multiplicity(indices, root_idx, root_idx)

    def do_sample_with_multiplicity(self, indices, root, new_root):
        author_list = self.children.get(root, [])
        author_it = iter(author_list)
        cur_author = next(author_it, None)
        indices_it = iter(indices)
        cur_idx = next(indices_it, None)
        cur_offset = 0
        while cur_idx != None and cur_author != None:
            # Compress the path to the new root
            if cur_author != new_root:
                self.parent[cur_author] = new_root

            end_window = cur_offset + self.cluster_size[cur_author]

            recursive_indices = []
            while cur_idx != None and cur_idx >= cur_offset and cur_idx < end_window:
                recursive_indices.append(cur_idx - cur_offset)
                cur_idx = next(indices_it, None)

            if recursive_indices:
                if self.cluster_size[cur_author] == 1:
                    yield cur_author
                else:
                    for x in self.do_sample_with_multiplicity(recursive_indices, cur_author, new_root):
                        yield x

            cur_offset = end_window
            cur_author = next(author_it, None)
        if cur_idx != None and cur_author == None:
            yield root

    def find(self, a):
        if self.parent[a] == None:
            return a
        elif self.parent[a] == a:
            print("WARNING: parent[a] = a, with a = "+str(a))
            return a
        else:
            res = self.find(self.parent[a])
            self.parent[a] = res
            return res

    def union(self, a, b):
        new_root = self.find(b)
        old_root = self.find(a)
        if new_root != old_root:
            self.parent[old_root] = new_root
            self.children[new_root].append(old_root)
            self.cluster_size[new_root] += self.cluster_size[old_root]
            self.num_relevant[new_root] += self.num_relevant[old_root]
            self.cluster_ids.discard(old_root)

    def computeRelevance(self, target):
        if not self.relevance_computed.get(target, False):
            dept_pk = self.researcher.department_id
            relevant = self.rc.classify(self.authors[target], dept_pk)
            parent = self.find(target)
            self.relevance[target] = relevant
            if relevant:
                self.num_relevant[parent] += 1
                if parent != target:
                    self.num_relevant[target] += 1
            self.relevance_computed[target] = relevant


    def runClustering(self, target, order_pk=False, logf=None):
        # TODO this method is supposed to update name.is_known if needed
        # for now, it is not required, but it will be when we introduce a
        # better name similarity function
        MAX_CLUSTER_SIZE_DURING_FETCH = 1000
        NB_TESTS_WITHIN_CLUSTER = 32

        # STEP 0: compute relevance
        self.computeRelevance(target)

        # STEP 1: clusters
        if order_pk:
            clusters = filter(lambda x: x < target, self.cluster_ids)
        else:
            clusters = self.clusters.copy()
        print("Number of clusters: "+str(len(clusters)))
        print(" ".join([str(self.cluster_size[x]) for x in clusters]))

        # STEP 2: for each cluster, compute similarity
        nb_edges_added = 0
        for cid in clusters:
            # print("C n°"+str(cid))
            to_check = self.sample_with_multiplicity(NB_TESTS_WITHIN_CLUSTER, cid)

            match_found = False
            for author in to_check:
                similar = self.classify(author, target)
                if similar:
                    print("   "+str(target)+"-"+str(author)+"\t"+str(similar))
                print(str(self.authors[author].pk)+"-"+
                        str(self.authors[target].pk)+"\t"+str(similar), file=logf)
                if similar:
                    match_found = True
                    self.similar[target] = author
                    # Merge the two clusters
                    self.union(target, author)
                    break
            if match_found:
                nb_edges_added += 1
        print(str(nb_edges_added)+" edges added")


    def outputGraph(self, outf):
        print('nodedef>name VARCHAR,label VARCHAR,pid VARCHAR,visibility VARCHAR,relevance VARCHAR', file=outf)
        for (x,v) in self.authors.items():
            visibility = v.paper.visibility
            if v.paper.year <= 2012:
                visibility = 'NOT_LABELLED'
            print(nocomma([x,unidecode(v.paper.title), v.paper.id,
                visibility, self.relevance.get(x,None)]), file=outf)
        print('edgedef>node1 VARCHAR,node2 VARCHAR', file=outf)
        for (x,y) in self.parent.items():
            if y != None:
                print(nocomma([x,y]), file=outf)


