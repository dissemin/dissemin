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



class ClusteringContext(object):
    def __init__(self, researcher, sc, rc):
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
        # The sum of the relevance scores of the indirect children
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

        author_queryset = self.getAuthorQuerySet()

        for author in author_queryset:
            self.addAuthor(author)

    def getAuthorQuerySet(self):
        """
        The queryset returning all the authors related to the researcher, sorted by id.
        Useful to populate the clustering context.
        """
        return Author.objects.filter(name__variant_of=self.researcher).filter(
                Q(paper__visibility='VISIBLE') | Q(paper__visibility='DELETED')).order_by('id')

    def addAuthor(self, author):
        """
        Add an author to the clustering context, setting up everything for the clustering.
        """
        pk = author.pk
        self.authors[pk] = author
        if pk == author.cluster_id:
            self.parent[pk] = None
        else:
            self.parent[pk] = author.cluster_id
        self.similar[pk] = author.similar
        self.children[pk] = filter(lambda x: x != pk, [child.pk for child in author.clusterrel.all()])
        if author.cluster_id == None or author.cluster_id == pk:
            self.cluster_ids.add(pk)
        self.author_data[pk] = self.sc.getDataById(pk)
        self.num_relevant[pk] = author.cluster_relevance
        self.cluster_size[pk] = author.num_children

    def checkGraph(self):
        """
        Debugging tool to inspect the state of the Union-Find data structure
        """
        for pk in self.parent:
            print('## '+str(pk))
            parent = self.parent[pk]
            if parent != None:
                print('Parent: '+str(parent))
            else:
                print('Cluster.')
            if self.cluster_size[pk] > 1:
                print('Cluster size: '+str(self.cluster_size[pk]))
            if self.children[pk]:
                print('Children: '+str(self.children[pk]))

    def commit(self):
        """
        Push the state of the graph to the database.
        """
        for (pk,val) in self.authors.items():
            val.cluster_id = self.find(pk)
            val.similar_id = self.similar.get(pk,None)
            val.num_children = self.cluster_size[pk]
            val.cluster_relevance = self.num_relevant[val.cluster_id]
            cluster_size = self.cluster_size[val.cluster_id]
            if self.num_relevant[val.cluster_id] > 0:
                val.researcher_id = self.researcher.id
            else:
                val.researcher_id = None
            # Num_relevant is not stored as it is department-centric
            # whereas the clusters themselves are "universal"
            val.save()

    def classify(self, pkA, pkB):
        """
        Compute the similarity between pkA and pkB.
        """
        # No need to cache as the algorithm already performs every test
        # at most once
        return self.sc.classifyData(self.author_data[pkA], self.author_data[pkB])

    def sample_with_multiplicity(self, nb_samples, root_idx):
        """
        Return nb_samples random samples from the cluster rooted in root_idx
        """
        population_size = self.cluster_size[root_idx]
        if nb_samples < population_size:
            nb_samples = min(nb_samples, population_size)
            indices = random.sample(xrange(population_size), nb_samples)
            indices.sort()
        else:
            indices = range(population_size)

        return self.do_sample_with_multiplicity(indices, root_idx, root_idx)

    def do_sample_with_multiplicity(self, indices, root, new_root):
        """
        Actual recursive function that does the job of sample_with_multiplicity
        """
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
                if self.cluster_size[cur_author] < 1:
                    print("Invalid cluster size detected")
                    raise ValueError('Invalid cluster size detected')
                elif self.cluster_size[cur_author] == 1:
                    yield cur_author
                else:
                    for x in self.do_sample_with_multiplicity(recursive_indices, cur_author, new_root):
                        yield x

            cur_offset = end_window
            cur_author = next(author_it, None)
        if cur_idx != None and cur_author == None:
            yield root

    def find(self, a):
        """
        This is the "Find" in "Union-Find":
        returns the id of the cluster an author belongs to.
        """
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
        """
        This is the "Union" in "Union-Find":
        Merges two clusters of authors.
        """
        new_root = self.find(b)
        old_root = self.find(a)
        if new_root != old_root:
            self.parent[old_root] = new_root
            self.children[new_root].append(old_root)
            self.cluster_size[new_root] += self.cluster_size[old_root]
            self.num_relevant[new_root] += self.num_relevant[old_root]
            self.cluster_ids.discard(old_root)

    def computeRelevance(self, target):
        """
        Compute the relevance of a given author.
        """
        if not self.relevance_computed.get(target, False):
            dept_pk = self.researcher.department_id
            relevance = self.rc.score(self.authors[target], dept_pk, True)
            parent = self.find(target)
            self.relevance[target] = relevance
            self.num_relevant[parent] += relevance
            if parent != target:
                self.num_relevant[target] += relevance
            self.relevance_computed[target] = True


    def runClustering(self, target, order_pk=False, logf=None):
        """
        Run the clustering algorithm for a given author.
        It compares the given target to other clusters and does the appropriate
        merges when a similarity is found.
        If order_pk, it will only be compared with clusters of lower pk.
        A log file can be provided in logf, the outcomes of the similarity classifier
        will be output there.
        """
        MAX_CLUSTER_SIZE_DURING_FETCH = 1000
        NB_TESTS_WITHIN_CLUSTER = 32

        # STEP 0: compute relevance
        self.computeRelevance(target)

        # STEP 1: clusters
        if order_pk:
            clusters = filter(lambda x: x < target, self.cluster_ids)
        else:
            clusters = filter(lambda x: x != target, self.cluster_ids)
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
                if logf:
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

    def reclusterBatch(self):
        """
        Reclusters everything!
        """
        pklist = list(self.parent)
        pklist.sort()

        print("Removing previous clustering output…")
        self.getAuthorQuerySet().update(
                researcher=None,
                cluster=None,
                num_children=1,
                cluster_relevance=0.,
                similar=None)
        print("Updating clustering context…")
        for pk in self.parent:
            self.parent[pk] = None
            self.num_relevant[pk] = 0.
            self.children[pk] = []
            self.cluster_ids.add(pk)
            self.cluster_size[pk] = 1

        logf = None
        idx = 0
        count = len(pklist)

        for a in self.getAuthorQuerySet():
            idx += 1
            print("# "+str(idx)+"/"+str(count)+" ## "+unicode(a.paper_id))
            self.runClustering(a.pk, True, logf)

        self.commit()

        graphf = open('learning/gephi/classified-'+str(self.researcher.pk)+'.gdf', 'w')
        self.outputGraph(graphf)
        graphf.close()           

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


# This structure stores clustering contextes for online clustering
class ClusteringContextFactory(object):
    """
    Creates and stores clustering contexts for each researcher.
    The contexts are created lazily.
    """
    def __init__(self, sc, rc):
        self.cc = dict()
        self.sc = sc
        self.rc = rc
        self.authors_to_cluster = []

    def load(self, researcher):
        if researcher.pk in self.cc:
            return
        # Otherwise we have to create a fresh one
        print('Loading clustering context for researcher '+str(researcher))
        context = ClusteringContext(researcher, self.sc, self.rc)
        self.cc[researcher.pk] = context

    def reclusterBatch(self, researcher):
        """
        Runs the algorithm on the whole set of papers related to a researcher
        Not suitable for online incremental update.
        """
        self.load(researcher)
        self.cc[researcher.pk].reclusterBatch()


    def clusterAuthorLater(self, author):
        potential_researchers = author.name.variant_of.all()
        for researcher in potential_researchers:
            self.clusterAuthorResearcherLater(author, researcher)

    def clusterAuthorResearcherLater(self, author, researcher):
        self.load(researcher)
        self.authors_to_cluster.append((author,researcher))

    def clusterAuthor(self, author, researcher):
        self.load(researcher)
        self.cc[researcher.pk].addAuthor(author)
        self.cc[researcher.pk].runClustering(author.pk)

    def clusterAuthorForAllResearchers(self, author):
        potential_researchers = author.name.variant_of.all()
        for researcher in potential_researchers:
            self.clusterAuthor(author, researcher)
    
    def clusterThemNow(self):
        for (author,researcher) in self.authors_to_cluster:
            self.clusterAuthor(author, researcher)
        authors_to_cluster = []
  
    def commitThemAll(self):
        self.clusterThemNow()
        for k in self.cc:
            self.cc[k].commit()
    


