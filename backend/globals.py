# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from os.path import isfile
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from backend.similarity import *
from backend.relevance import *
from backend.clustering import *
from papers.models import Author

clustering_context_factory = None

if isfile('models/similarity.pkl'):
    print("Loading similarity classifier…")
    similarity_classifier = SimilarityClassifier(filename='models/similarity.pkl')
    relevance_classifier = OrcidRelevanceClassifier()
    clustering_context_factory = ClusteringContextFactory(similarity_classifier,
        relevance_classifier)
else:
    print('Not loading classifiers as they have not been trained.')

def get_ccf():
    global clustering_context_factory
    return clustering_context_factory

@receiver(post_save, sender=Author, dispatch_uid='onAuthorSaved')
def onAuthorSaved(sender, **kwargs):
    """
    Callback called after an :class:`Author` is saved.
    Adds it to the relevant clustering context if needed.
    """
    if clustering_context_factory is None or not kwargs['created']:
        return

    a = kwargs['instance']

    a.update_name_variants_if_needed()
    if a.name.is_known:
        try:
            a = Author.objects.get(pk=a.pk)
        except Author.DoesNotExist:
            print ("INVALID author in onAuthorSaved %d" % a.pk)
        clustering_context_factory.clusterAuthorLater(a)

@receiver(pre_delete, sender=Author, dispatch_uid='onAuthorDeleted')
def onAuthorDeleted(sender, **kwargs):
    """
    Callback called after an :class:`Author` is deleted.
    Removes it from the clustering context, notifies its parent
    that it has lost a child.
    """
    a = kwargs['instance']
    if a.cluster_id is not None and a.cluster_id != a.id:
        cluster = a.cluster
        cluster.num_children -= a.num_children
        cluster.cluster_relevance -= a.cluster_relevance
        cluster.save(update_fields=['num_children','cluster_relevance'])
    if a.num_children > 1:
        # We need to attach these children to a new author!
        new_root = None
        if a.cluster_id is not None and a.cluster_id != a.id:
            # We already have a parent
            new_root = a.cluster_id
        else:
            # We need a new root, let's choose it among the children
            # TODO
            new_root = None

    if clustering_context_factory is None:
        return
    clustering_context_factory.deleteAuthor(a.pk)

