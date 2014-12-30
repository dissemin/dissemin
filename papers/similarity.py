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
from papers.utils import match_names, iunaccent, nocomma, filter_punctuation
from nltk.tokenize.punkt import PunktWordTokenizer
from sklearn import svm
from sklearn.metrics import confusion_matrix
import cPickle
import numpy as np
import matplotlib.pyplot as plt
from unidecode import unidecode

punktTokenizer = PunktWordTokenizer()

def tokenize(l):
    return punktTokenizer.tokenize(iunaccent(l))

def jaccard(setA, setB):
    inter = setA & setB
    union = setA | setB
    if union:
        return float(len(inter)) / len(union)
    else:
        return 1.

class SimilarityFeature(object):
    """
    A feature for a binary classifier: given two authors,
    do they represent the same person?
    """
    def __init__(self):
        pass

    def compute(self, authorA, authorB):
        return 0.


class CoauthorsSimilarity(SimilarityFeature):
    """
    Number of matching coauthors (without the target authors themselves)
    TODO: use Invenio's name similarity algorithm to refine this.
    """
    def __init__(self):
        super(CoauthorsSimilarity, self).__init__()
    
    def compute(self, authorA, authorB):
        coauthorsA = authorA.paper.author_set.exclude(id=authorA.id)
        coauthorsB = authorB.paper.author_set.exclude(id=authorB.id)
        score = 0.
        for a in coauthorsA:
            for b in coauthorsB:
                name_a = a.name
                name_b = b.name
                if match_names((name_a.first,name_a.last),(name_b.first, name_b.last)):
                    score += 1.
        return score

def intersectionScore(model, strA, strB, explain=False):
    """
    Returns the sum of the -log scores of the common words in the two strings
    """
    threshold = 4
    wordsA = set(filter_punctuation(tokenize(strA)))
    wordsB = set(filter_punctuation(tokenize(strB)))
    intersection = wordsA & wordsB
    union = wordsA | wordsB
    if explain:
        for w in intersection:
            print(w+'\t'+str(model.lp(w)))
    wordScores = map(model.lp, intersection)
    wordScores = filter(lambda lp: -lp >= threshold, wordScores)
    interScore = -sum(wordScores)
    return interScore# / len(union)


class TitleSimilarity(SimilarityFeature):
    """
    Similarity between the titles
    """
    def __init__(self, languageModel):
        super(TitleSimilarity, self).__init__()
        self.languageModel = languageModel

    def compute(self, authorA, authorB, explain=False):
        ta = authorA.paper.title
        tb = authorB.paper.title
        return intersectionScore(self.languageModel, ta, tb, explain)

class ContributorsSimilarity(SimilarityFeature):
    """
    Similarity between the contributors (institutions according to HAL)
    """
    def __init__(self, languageModel):
        super(ContributorsSimilarity, self).__init__()
        self.languageModel = languageModel

    def compute(self, authorA, authorB, explain=False):
        contributorsA = [r.contributors for r in authorA.paper.oairecord_set.all()]
        contributorsB = [r.contributors for r in authorB.paper.oairecord_set.all()]
        contributorsA = filter(lambda x: x != None, contributorsA)
        contributorsB = filter(lambda x: x != None, contributorsB)
        ta = ' '.join(contributorsA)
        tb = ' '.join(contributorsB)
        return intersectionScore(self.languageModel, ta, tb, explain)


class PublicationSimilarity(SimilarityFeature):
    """
    Similarity between the publications associated to the two papers.
    The keywords provided through OAI-PMH are also taken into account.
    """
    def __init__(self, languageModel):
        super(PublicationSimilarity, self).__init__()
        self.languageModel = languageModel

    def compute(self, authorA, authorB, explain=False):
        pubsA = authorA.paper.publication_set.all()
        pubsB = authorB.paper.publication_set.all()
        allA = [a.full_title() for a in pubsA]
        for r in authorA.paper.oairecord_set.all():
            if r.keywords:
                allA.append(r.keywords)
        allB = [a.full_title() for a in pubsB]
        for r in authorB.paper.oairecord_set.all():
            if r.keywords:
                allB.append(r.keywords)

        nbPairs = 0
        totalScore = 0.
        for ta in allA:
            for tb in allB:
                nbPairs += 1
                if ta == tb:
                    totalScore += 40.0
                    # maxScore = max(40.0,maxScore)
                else:
                    totalScore += intersectionScore(self.languageModel, ta, tb, explain)
              
        if nbPairs:
            return totalScore / nbPairs
        else:
            return 0.

class SimilarityClassifier(object):
    def __init__(self, **kwargs):
        if 'filename' in kwargs:
            self.load(kwargs['filename'])
            return
        elif not 'languageModel' in kwargs:
            raise ValueError('A language model has to be provided.')
        publicationModel = kwargs['languageModel']
        contributorsModel = kwargs.get('contributorsModel', publicationModel)
        if not contributorsModel:
            contributorsModel = publicationModel
        self.simFeatures = [
                CoauthorsSimilarity(),
                PublicationSimilarity(publicationModel),
                TitleSimilarity(publicationModel),
                ContributorsSimilarity(contributorsModel),
                ]
        self.classifier = None
        self.positiveSampleWeight = 0.15
    
    def _computeFeatures(self, authorA, authorB):
        features = []
        for f in self.simFeatures:
            features.append(f.compute(authorA, authorB))
        return features

    def _toAuthorPairs(self, author_ids):
        authors = [(Author.objects.get(pk=ida),Author.objects.get(pk=idb)) for (ida,idb) in author_ids]
        return authors

    def _toFeaturePairs(self, authors):
        features = [self._computeFeatures(a,b) for (a,b) in authors]
        return features
  
    def train(self, features, labels, kernel='rbf'):
        self.classifier = svm.SVC(kernel=str(kernel))
        weights = [(self.positiveSampleWeight if label else 1.) for label in labels]
        self.classifier.fit(features, labels, sample_weight=weights)

    def confusion(self, features, labels):
        if not self.classifier:
            return None
        pred = self.classifier.predict(features)
        return confusion_matrix(pred, labels)

    def classify(self, authorA, authorB):
        if not self.classifier:
            return None
        feat_vec = self._computeFeatures(authorA, authorB)
        output = self.classifier.predict(feat_vec)
        return output[0]

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

    def outputGraph(self, author_set, outfile, logf):
        print('nodedef>name VARCHAR,label VARCHAR,pid VARCHAR,visibility VARCHAR', file=outfile)
        for author in author_set:
            paper = author.paper
            visibility = paper.visibility
            if paper.year <= 2012:
                visibility = 'NOT_LABELLED'
            print(nocomma([author.pk, unidecode(paper.title), paper.id, visibility]), file=outfile)
        print('edgedef>node1 VARCHAR,node2 VARCHAR', file=outfile)
        authors = list(author_set)
        for i in range(len(authors)):
            for j in range(i):
                output = self.classify(authors[i],authors[j])
                print(str(authors[i].pk)+"-"+str(authors[j].pk)+"\t"+str(output), file=logf)
                if output: 
                    print(nocomma([authors[i].pk,authors[j].pk]), file=outfile)

    def load(self, fname):
        f = open(fname, 'rb')
        dct = cPickle.load(f)
        f.close()
        self.__dict__.update(dct)

    def save(self, fname):
        f = open(fname, 'wb')
        cPickle.dump(self.__dict__, f)
        f.close()
 


