# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import cPickle
from gensim.models import *
from papers.utils import tokenize

class LDATopicModel(object):
    """
    Maps a paper to a vector, representing its topics
    """
    def __init__(self, **kwargs):
        """
        Either builds the model from a pretrained dictionary and LDA model
        (arguments 'dictionary' and 'model')
        or trains a fresh model from a corpus (argument 'corpus')
        """
        if 'dictionary' in kwargs:
            self.dct = kwargs['dictionary']
        if 'model' in kwargs:
            self.lda = kwargs['model']
        if 'corpus' in kwargs:
            corpus = kwargs['corpus']
            self.lda = LdaModel(corpus, num_topics=kwargs.get('n_topics', 100))
            self.dct = corpus.dictionary

    def load(self, fname):
        """
        Loads the model from a file
        """
        with open(fname, 'rb') as f:
            dct = cPickle.load(f)
        self.__dict__.update(dct)
        self.lda = LdaModel.load(f+'.model')
    
    def save(self, fname):
        """
        Saves the model to a file
        """
        self.lda.save(f+'.model')
        with open(fname, 'wb') as f:
            copy = self.__dict__.copy()
            if 'lda' in copy:
                del copy['lda']
            cPickle.dump(copy, f)
        f.close()

    def print_topics(self, n_topics=10):
        """
        For debugging purposes: prints some topics from the model
        """
        for topic in self.lda.show_topics(n_topics, formatted=False):
            print self._print_topic(topic)

    def _print_topic(self, topic):
        words = [(f, self.dct[int(x)]) for (f,x) in topic]
        return (' + '.join(['%.3f*%s' % v for v in words])).encode('utf-8')

    def get_distr(self, string, debug=False):
        # Tokenize
        words = tokenize(string)

        # To BOW
        bow = self.dct.doc2bow(words)

        # To topics
        distr = self.lda[bow]
        if debug:
            for (topic_id,value) in distr[:10]:
                print "Topic id %d, value %.3f" % (topic_id,value)
                print self._print_topic(self.lda.show_topic(topic_id))

        return distr


