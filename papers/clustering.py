# -*- encoding: utf-8 -*-
from __future__ import unicode_literals, print_function

from papers.similarity import SimilarityClassifier
from papers.models import Author
import random

# authorSimilarityClassifier = SimilarityClassifier(filename='models/similarity.pkl')

class ClusteringContext(object):
    def __init__(self, author_queryset, sc):
        """
        Caveat: the author_queryset has to be closed under the "children" relation.
        """
        self.authors = dict()
        self.parent = dict()
        self.similar = dict()
        self.children = dict()
        self.cluster_ids = set()
        self.sc = sc
        self.author_data = dict()
        for author in author_queryset:
            pk = author.pk
            self.authors[pk] = author
            self.parent[pk] = author.cluster_id
            self.similar[pk] = author.similar
            self.children[pk] = [child.pk for child in author.clusterrel.all()]
            if author.cluster_id == None:
                self.cluster_ids.add(pk)
            self.author_data[pk] = sc.getDataById(pk)

    def commit(self):
        for (pk,val) in self.authors.items():
            val.cluster_id = self.find(pk)
            val.num_children = self.num_children[pk]
            val.similar_id = self.similar[pk]
            val.save()

    def num_children(self, pk):
        return len(self.children.get(pk,0))+1

    def classify(self, pkA, pkB):
        # No need to cache as the algorithm already performs every test
        # at most once
        return self.sc.classifyData(self.author_data[pkA], self.author_data[pkB])

    def sample_with_multiplicity(self, nb_samples, root_idx):
        population_size = self.num_children(root_idx)
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
            self.parent[cur_author] = new_root

            end_window = cur_offset + self.num_children(cur_author)

            recursive_indices = []
            while cur_idx != None and cur_idx >= cur_offset and cur_idx < end_window:
                recursive_indices.append(cur_idx - cur_offset)
                cur_idx = next(indices_it, None)

            if recursive_indices:
                if self.num_children(cur_author) == 1:
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
            self.cluster_ids.discard(old_root)

    def runClustering(self, target, order_pk=False, logf=None):
        # TODO this method is supposed to update name.is_known if needed
        # for now, it is not required, but it will be when we introduce a
        # better name similarity function
        MAX_CLUSTER_SIZE_DURING_FETCH = 1000
        NB_TESTS_WITHIN_CLUSTER = 10 # if clusters are 2/3-quasicliques,
        # it yields a proba of less than 0.01 to miss a match

        # STEP 1: clusters
        if order_pk:
            clusters = filter(lambda x: x < target, self.cluster_ids)
        else:
            clusters = self.clusters.copy()
        print("Number of clusters: "+str(len(clusters)))
        print(" ".join([str(self.num_children(x)) for x in clusters]))

        # STEP 2: for each cluster, compute similarity
        nb_edges_added = 0
        for cid in clusters:
            print("C n°"+str(cid))
            cluster_contents = self.children[cid]
            to_check = self.sample_with_multiplicity(NB_TESTS_WITHIN_CLUSTER, cid)
            # to_check = random.sample(cluster_contents, nb_tests)
            match_found = False
            for author in to_check:
                similar = self.classify(author, target)
                print("   "+str(target)+"-"+str(author)+"\t"+str(similar))
                print(str(self.authors[author].pk)+"-"+str(self.authors[target].pk)+"\t"+str(similar), file=logf)
                if similar:
                    match_found = True
                    self.similar[target] = author
                    # Merge the two clusters
                    self.union(target, author)
                    break
            if match_found:
                nb_edges_added += 1
        print(str(nb_edges_added)+" edges added")

        # STEP 3: if we have ended up in a cluster associated with a researcher, fine

        # STEP 4: if not, we classify this record
        # TODO

        # STEP 5: if it should be kept, then we propagate it to the rest of the cluster



