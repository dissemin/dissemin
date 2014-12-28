# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.similarity import SimilarityClassifier
from papers.models import Author
import random

authorSimilarityClassifier = SimilarityClassifier(filename='models/similarity.pkl')

def sample_with_multiplicity(nb_samples, author_list, root):
    population_size = sum([x.num_children for x in author_list])+1
    if nb_samples < population_size:
        nb_samples = min(nb_samples, population_size)
        indices = random.sample(xrange(population_size), nb_samples)
        indices.sort()
    else:
        indices = range(population_size)

    return do_sample_with_multiplicity(indices, author_list, root, root)

def do_sample_with_multiplicity(indices, author_list, root, new_root):
    author_it = iter(author_list)
    cur_author = next(author_it, None)
    indices_it = iter(indices)
    cur_idx = next(indices_it, None)
    cur_offset = 0
    while cur_idx != None and cur_author != None:
        # Compress the path to the new root
        if cur_author.cluster_id != new_root.id:
            cur_author.cluster = new_root
            cur_author.save(update_fields=['cluster'])

        end_window = cur_offset + cur_author.num_children

        recursive_indices = []
        while cur_idx != None and cur_idx >= cur_offset and cur_idx < end_window:
            recursive_indices.append(cur_idx - cur_offset)
            cur_idx = next(indices_it, None)

        if recursive_indices:
            if cur_author.num_children == 1:
                yield cur_author
            else:
                recursive_author_list = list(Author.objects.filter(cluster_id=cur_author.id))
                for x in do_sample_with_multiplicity(recursive_indices, recursive_author_list, cur_author, new_root):
                    yield x

        cur_offset = end_window
        cur_author = next(author_it, None)    
    if cur_idx != None and cur_author == None:
        yield root

def runClustering(to_cluster):
    # TODO this method is supposed to update name.is_known if needed
    # for now, it is not required, but it will be when we introduce a
    # better name similarity function
    MAX_CLUSTER_SIZE_DURING_FETCH = 1000
    NB_TESTS_WITHIN_CLUSTER = 10 # if clusters are 2/3-quasicliques,
    # it yields a proba of less than 0.01 to miss a match

    # STEP 1: find the clusters associated to the target name
    clusters = to_cluster.name.author_set.filter(cluster__isnull=True, id__lt=to_cluster.id)
    cluster_ids = [x.pk for x in clusters]
    print "Number of clusters: "+str(len(cluster_ids))
    

    # STEP 2: for each cluster, compute similarity
    nb_edges_added = 0
    for cid in cluster_ids:
        cluster_contents = list(Author.objects.filter(cluster_id=cid)[:MAX_CLUSTER_SIZE_DURING_FETCH])
        cluster_root = Author.objects.get(pk=cid)
        to_check = sample_with_multiplicity(NB_TESTS_WITHIN_CLUSTER, cluster_contents, cluster_root)
        #to_check = random.sample(cluster_contents, nb_tests)
        match_found = False
        for author in to_check:
            similar = authorSimilarityClassifier.classify(to_cluster, author)
            if similar:
                match_found = True
                to_cluster.similar = author
                to_cluster.save(update_fields=['similar']) # maybe we can mutualize this save with the merge
                
                # Merge the two clusters
                to_cluster.merge_with(author)
                break
        if match_found:
            nb_edges_added += 1
    print str(nb_edges_added)+" edges added"

    # STEP 3: if we have ended up in a cluster associated with a researcher, fine
    cur_cluster = to_cluster.get_cluster()
    if cur_cluster.researcher:
        return

    # STEP 4: if not, we classify this record
    # TODO

    # STEP 5: if it should be kept, then we propagate it to the rest of the cluster



