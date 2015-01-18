# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from __future__ import unicode_literals, print_function

from papers.models import Name, Author, Researcher
from papers.utils import iunaccent, nocomma, filter_punctuation, tokenize
from papers.names import match_names
from learning.model import WordCount
from sklearn import svm
from sklearn.metrics import confusion_matrix
import cPickle
import numpy as np
import matplotlib.pyplot as plt
from unidecode import unidecode

class RelevanceFeature(object):
    """
    A feature for a binary classifier: given an author and a department,
    does this person belong to this department?
    """
    def __init__(self):
        """
        Parameters should be set here.
        """
        pass

    def compute(self, author, dpt_id, explain=False):
        """
        Returns the value of the feature for the given author.
        """
        return 0.

class KnownCoauthors(RelevanceFeature):
    """
    Returns the number of known coauthors in the paper.
    TODO: The department is currently ignored. (not sure it is a problem)
    """
    def __init__(self):
        super(KnownCoauthors, self).__init__()

    def compute(self, author, dpt_id, explain=False):
        coauthors = author.paper.author_set.exclude(id=author.id).select_related('name')
        count = 0
        for a in coauthors:
            if a.researcher != None:
                count += 1
                if explain:
                    print('      '+unicode(a))
        if explain:
            print('   Common coauthors: '+str(count))
        return float(count)

class TopicalRelevanceFeature(RelevanceFeature):
    """
    General class for topic-based features.
    """
    def __init__(self, languageModel, **kwargs):
        super(TopicalRelevanceFeature, self).__init__()
        self.lang = languageModel
        self.models = dict()
        if 'filename' in kwargs:
            self.load(kwargs['filename'])

    def _wScore(self, line, dpt_id, explain=False):
        topicScore = self.models[dpt_id].lProbLine(line)
        langScore = self.lang.lProbLine(line)
        words = tokenize(line)
        if explain:
            for w in words:
                a = self.models[dpt_id].lp(w)
                b = self.lang.lp(w)
                print('      '+w+'\t'+str(a)+'-'+str(b)+' = '+str(a-b))
        return topicScore - langScore

    def _normalizedWScore(self, line, dpt_id, explain=False):
        topicScore = self.models[dpt_id].nlProbLine(line)
        langScore = self.lang.nlProbLine(line)
        if explain:
            words = tokenize(line)
            for w in words:
                a = self.models[dpt_id].lp(w)
                b = self.lang.lp(w)
                print('      '+w+'\t'+str(a)+'-'+str(b)+' = '+str(a-b))
        return topicScore - langScore


    def load(self, filename):
        f = open(filename, 'rb')
        dct = cPickle.load(f)
        f.close()
        self.__dict__.update(dct)

    def save(self, filename):
        f = open(filename, 'wb')
        cPickle.dump(self.__dict__, f)
        f.close()

    def feedLine(self, line, dpt_id):
        if line == None:
            return
        if dpt_id not in self.models:
            self.models[dpt_id] = WordCount()
        self.models[dpt_id].feedLine(line)

class TitleRelevance(TopicalRelevanceFeature):
    """
    Relevance of the title regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(TitleRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, dpt_id):
        self.feedLine(author.paper.title, dpt_id)

    def compute(self, author, dpt_id, explain=False):
        if dpt_id not in self.models:
            print("Warning, scoring a title for an unknown department")
            return 0.
        return self._normalizedWScore(author.paper.title, dpt_id, explain)

class PublicationRelevance(TopicalRelevanceFeature):
    """
    Relevance of the publications regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(PublicationRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, dpt_id):
        for pub in author.paper.publication_set.all().select_related('journal'):
            self.feedLine(pub.full_title(), dpt_id)

    def compute(self, author, dpt_id, explain=False):
        if dpt_id not in self.models:
            print("Warning, scoring a publication for an unknown department id "+str(dpt_id))
            return 0.
        titles = [pub.full_title() for pub in author.paper.publication_set.all().select_related('journal')]
        if titles:
            return max(map(lambda t: self._normalizedWScore(t, dpt_id, explain), titles))
        return 0.

class KeywordsRelevance(TopicalRelevanceFeature):
    """
    Relevance of the publications regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(KeywordsRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, dpt_id):
        for record in author.paper.oairecord_set.all():
            self.feedLine(record.keywords, dpt_id)

    def compute(self, author, dpt_id, explain=False):
        if dpt_id not in self.models:
            print("Warning, scoring an oairecord for an unknown department id "+str(dpt_id))
            return 0.
        words = [rec.keywords for rec in author.paper.oairecord_set.all()]
        words = filter(lambda x: x != None, words)
        return float(sum(map(lambda t: self._normalizedWScore(t, dpt_id, explain), words)))

class ContributorsRelevance(TopicalRelevanceFeature):
    """
    Relevance of the contributors regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(ContributorsRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, dpt_id):
        for record in author.paper.oairecord_set.all():
            self.feedLine(record.contributors, dpt_id)

    def compute(self, author, dpt_id, explain=False):
        if dpt_id not in self.models:
            print("Warning, scoring contributors for an unknown department id "+str(dpt_id))
            return 0.
        words = [rec.contributors for rec in author.paper.oairecord_set.all()]
        words = filter(lambda x: x != None, words)
        return float(sum(map(lambda t: self._normalizedWScore(t, dpt_id, explain), words)))

class RelevanceClassifier(object):
    def __init__(self, **kwargs):
        if 'filename' in kwargs:
            self.load(kwargs['filename'])
            return
        elif 'languageModel' not in kwargs:
            raise ValueError("A language model is required.")
        lm = kwargs['languageModel']
        cm = kwargs.get('contributorsModel', lm)
        pm = kwargs.get('publicationsModel', lm)
        self.features = [
                KnownCoauthors(),
                TitleRelevance(lm),
                KeywordsRelevance(lm),
                PublicationRelevance(pm),
                ContributorsRelevance(cm),
                ]
        self.classifier = None
        self.positiveSampleWeight = 1.0
    
    def computeFeatures(self, author, dpt_id, explain=False):
        if explain:
            for i in range(len(self.features)):
                print('   Feature '+str(i))
                f = self.features[i]
                f.compute(author, dpt_id, True)
        return map(lambda f: f.compute(author, dpt_id), self.features)

    def train(self, features, labels, kernel='rbf'):
        self.classifier = svm.SVC(kernel=str(kernel))
        weights = [(self.positiveSampleWeight if label else 1.) for label in labels]
        self.classifier.fit(features, labels, sample_weight=weights)

    def confusion(self, features, labels):
        if not self.classifier:
            return None
        pred = self.classifier.predict(features)
        return confusion_matrix(pred, labels)

    def classify(self, author, dpt_id):
        if not self.classifier:
            return None
        features = self.computeFeatures(author, dpt_id)
        output = self.classifier.predict(features)
        return output[0]

    def feed(self, author, dpt_id):
        for f in self.features:
            if isinstance(f, TopicalRelevanceFeature):
                f.feed(author, dpt_id)

    def plotClassification(self, features, labels):
        h = 0.1
        X = np.array(features)
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                                     np.arange(y_min, y_max, h))
        Z = self.classifier.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        plt.contourf(xx, yy, Z, cmap=plt.cm.Paired, alpha=0.8)
        plt.scatter(X[:, 0], X[:, 1], c=labels, cmap=plt.cm.Paired, alpha=1.0)
        plt.xlim(xx.min(), xx.max())
        plt.ylim(yy.min(), yy.max())
        plt.xticks(())
        plt.yticks(())
        plt.show()

    def load(self, fname):
        f = open(fname, 'rb')
        dct = cPickle.load(f)
        f.close()
        self.__dict__.update(dct)

    def save(self, fname):
        f = open(fname, 'wb')
        cPickle.dump(self.__dict__, f)
        f.close()
 

