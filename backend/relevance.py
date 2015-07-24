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

from sklearn import svm
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import StandardScaler
import cPickle
import numpy as np
from unidecode import unidecode
from django.core.exceptions import ObjectDoesNotExist

from papers.models import Name, Author, Researcher, NameVariant
from papers.utils import iunaccent, nocomma, filter_punctuation, tokenize
from papers.name import to_plain_name, name_similarity

from learning.model import WordCount

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

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

    def compute(self, author, researcher, explain=False):
        """
        Returns the value of the feature for the given author.
        """
        return [0.]

class KnownCoauthors(RelevanceFeature):
    """
    Returns the number of known coauthors in the paper.
    TODO: The department is currently ignored. (not sure it is a problem)
    """
    def __init__(self):
        super(KnownCoauthors, self).__init__()

    def compute(self, author, researcher, explain=False):
        coauthors = author.paper.author_set.exclude(id=author.id).select_related('name')
        count = 0
        nb_coauthors = 0
        for a in coauthors:
            nb_coauthors += a.name.best_confidence
            count += 1
            if explain and a.name.is_known:
                print('      '+unicode(a))
        if explain:
            print('   Common coauthors: '+str(count)+', total '+str(nb_coauthors))
        return [float(count),float(nb_coauthors)] 

class AuthorNameSimilarity(RelevanceFeature):
    """
    The similarity of the target name with the reference name for the researcher
    """
    def __init__(self):
        super(AuthorNameSimilarity, self).__init__()

    def compute(self, author, researcher, explain=False):
        try:
            return [author.name.best_confidence]
        except ObjectDoesNotExist:
            return [0.]

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

    def _wScore(self, line, researcher, explain=False):
        topicScore = self.models[researcher.department_id].lProbLine(line)
        langScore = self.lang.lProbLine(line)
        words = tokenize(line)
        if explain:
            for w in words:
                a = self.models[researcher.department_id].lp(w)
                b = self.lang.lp(w)
                print('      '+w+'\t'+str(a)+'-'+str(b)+' = '+str(a-b))
        return topicScore - langScore

    def _normalizedWScore(self, line, researcher, explain=False):
        topicScore = self.models[researcher.department_id].nlProbLine(line)
        langScore = self.lang.nlProbLine(line)
        if explain:
            words = tokenize(line)
            for w in words:
                a = self.models[researcher.department_id].lp(w)
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

    def feed(self, author, researcher):
        self.feedLine(author.paper.title, researcher.department_id)

    def compute(self, author, researcher, explain=False):
        if researcher.department_id not in self.models:
            print("Warning, scoring a title for an unknown department")
            return [0.]
        return [self._normalizedWScore(author.paper.title, researcher, explain)]

class PublicationRelevance(TopicalRelevanceFeature):
    """
    Relevance of the publications regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(PublicationRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, researcher):
        for pub in author.paper.publication_set.all().select_related('journal'):
            self.feedLine(pub.full_title(), researcher.department_id)

    def compute(self, author, researcher, explain=False):
        if researcher.department_id not in self.models:
            print("Warning, scoring a publication for an unknown department id "+str(researcher.department_id))
            return [0.]
        titles = [pub.full_title() for pub in author.paper.publication_set.all().select_related('journal')]
        if titles:
            return [max(map(lambda t: self._normalizedWScore(t, researcher, explain), titles))]
        return [0.]

class KeywordsRelevance(TopicalRelevanceFeature):
    """
    Relevance of the publications regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(KeywordsRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, researcher):
        for record in author.paper.oairecord_set.all():
            self.feedLine(record.keywords, researcher.department_id)

    def compute(self, author, researcher, explain=False):
        if researcher.department_id not in self.models:
            print("Warning, scoring an oairecord for an unknown department id "+str(researcher.department_id))
            return [0.]
        words = [rec.keywords for rec in author.paper.oairecord_set.all()]
        words = filter(lambda x: x != None, words)
        return [float(sum(map(lambda t: self._normalizedWScore(t, researcher, explain), words)))]

class ContributorsRelevance(TopicalRelevanceFeature):
    """
    Relevance of the contributors regarding the department
    """
    def __init__(self, lm, **kwargs):
        super(ContributorsRelevance, self).__init__(lm, **kwargs)

    def feed(self, author, researcher):
        for record in author.paper.oairecord_set.all():
            self.feedLine(record.contributors, researcher.deparmtent_id)

    def compute(self, author, researcher, explain=False):
        if researcher.department_id not in self.models:
            print("Warning, scoring contributors for an unknown department id "+str(researcher.department_id))
            return 0.
        words = [rec.contributors for rec in author.paper.oairecord_set.all()]
        words = filter(lambda x: x != None, words)
        return [float(sum(map(lambda t: self._normalizedWScore(t, researcher, explain), words)))]

class OrcidRelevance(RelevanceFeature):
    """
    Returns 1 when the ORCID of the author and the researcher match, 0 otherwise
    """
    def __init__(self):
        super(OrcidRelevance, self).__init__()

    def compute(self, author, researcher, explain=False):
        if explain:
            if author.affiliation == researcher.orcid:
                print("ORCID match")
            else:
                print("ORCID mismatch")
        if author.affiliation == researcher.orcid:
            return [1.]
        return [0.]


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
                AuthorNameSimilarity(),
                KnownCoauthors(),
                TitleRelevance(lm),
                KeywordsRelevance(lm),
                PublicationRelevance(pm),
                ContributorsRelevance(cm),
                ]
        self.classifier = None
        self.scaler = None
        self.positiveSampleWeight = 1.0
    
    def computeFeatures(self, author, researcher, explain=False):
        if explain:
            for i in range(len(self.features)):
                print('   Feature '+str(i))
                f = self.features[i]
                f.compute(author, researcher, True)
        return flatten(map(lambda f: f.compute(author, researcher), self.features))

    def train(self, features, labels, kernel='rbf'):
        self.classifier = svm.SVC(kernel=str(kernel))
        self.scaler = StandardScaler()
        self.scaler.fit(features)
        scaled_features = self.scaler.transform(features)
        weights = [(self.positiveSampleWeight if label else 1.) for label in labels]
        self.classifier.fit(scaled_features, labels, sample_weight=weights)

    def confusion(self, features, labels):
        if not self.classifier:
            return None
        scaled = self.scaler.transform(features)
        pred = self.classifier.predict(scaled)
        return confusion_matrix(pred, labels)

    def classify(self, author, researcher, verbose=False):
        distance = self.score(author, researcher, verbose)
        if distance:
            return distance > 0.

    def score(self, author, researcher, verbose=False):
        """
        Returns the distance (value of the decision function)
        for an author. An author is relevant when its distance
        is positive.
        """
        if not self.classifier:
            return None
        features = self.computeFeatures(author, researcher)
        scaled = self.scaler.transform([features])
        resp = self.classifier.decision_function(scaled)
        distance = resp[0]
        if verbose:
            print(str(features)+' -> '+str(distance))
        return distance

    def feed(self, author, researcher):
        for f in self.features:
            if isinstance(f, TopicalRelevanceFeature):
                f.feed(author, researcher)

    def plotClassification(self, features, labels):
        # TODO this is broken: no scaling
        import matplotlib.pyplot as plt
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
 
class DummyRelevanceClassifier(RelevanceClassifier):
    """
    Tries to do its best without relying on department-specific
    topic models
    """
    def __init__(self, **kwargs):
        self.features = [
                AuthorNameSimilarity(),
                KnownCoauthors()
                ]

    def score(self, author, researcher, verbose=False):
        features = self.computeFeatures(author, researcher, verbose)
        if features[0] >= 1.0: # author name similarity
            return features[1] # nb of known coauthors
        return -0.1

class AllRelevantClassifier(RelevanceClassifier):
    """
    Returns a positive similarity score for all papers
    """
    def __init__(self, **kwargs):
        pass

    def score(self, author, researcher, verbose=False):
        return 1.0

class SimpleRelevanceClassifier(RelevanceClassifier):
    """
    A relevance classifier that does not require any topical feature,
    but designed to be a bit better than the Dummy one
    (trainable)
    """
    def __init__(self, **kwargs):
        if 'filename' in kwargs:
            self.load(kwargs['filename'])
            return
        self.features = [
                AuthorNameSimilarity(),
                KnownCoauthors(),
                ]
        self.classifier = None
        self.positiveSampleWeight = 1.0
 
class OrcidRelevanceClassifier(RelevanceClassifier):
    """
    Returns relevance 1 when ORCID ids match,
    and a small negative score otherwise
    """
    def __init__(self, **kwargs):
        self.features = [
                OrcidRelevance(),
                AuthorNameSimilarity(),
                ]

    def score(self, author, researcher, verbose=False):
        features = self.computeFeatures(author, researcher, verbose)

        if not researcher.empty_orcid_profile: # if we found at least one record in the orcid profile
            if features[0] >= 0.5: # if the ORCIDs match
                return 10.0 # then we give a very good confidence
            return 0.1*(features[1]-2) # otherwise a slightly negative confidence
        else: # otherwise we don't know any publication for sure…
            return features[1] - 0.5



