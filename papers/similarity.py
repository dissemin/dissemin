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
from papers.utils import match_names, iunaccent
from nltk.tokenize.punkt import PunktWordTokenizer
from sklearn import svm
from sklearn.metrics import confusion_matrix
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

class PublicationSimilarity(SimilarityFeature):
    """
    Similarity between the publications associated to the two papers
    """
    def __init__(self, languageModel):
        super(PublicationSimilarity, self).__init__()
        self.languageModel = languageModel

    def compute(self, authorA, authorB, explain=False):
        pubsA = authorA.paper.publication_set.all()
        pubsB = authorB.paper.publication_set.all()
        nbPubPairs = 0
        totalScore = 0.
        for a in pubsA:
            for b in pubsB:
                nbPubPairs += 1
                ta = a.full_title()
                tb = b.full_title()
                if ta == tb:
                    totalScore += 50.0
                else:
                    wordsA = set(tokenize(ta))
                    wordsB = set(tokenize(tb))
                    intersection = wordsA & wordsB
                    union = wordsA | wordsB
                    if explain:
                        for w in intersection:
                            print(w+'\t'+str(self.languageModel.lp(w)))
                    interScore = -sum([self.languageModel.lp(w) for w in intersection])
                    totalScore += interScore# / len(union)
        if nbPubPairs:
            return totalScore / nbPubPairs
        else:
            return 0.

def nocomma(lst):
    lst = map(lambda x: str(x).replace(',','').replace('\n',''), lst)
    lst = [x if x else ' ' for x in lst]
    return ','.join(lst)

class SimilarityClassifier(object):
    def __init__(self, publicationModel):
        self.simFeatures = [CoauthorsSimilarity(), PublicationSimilarity(publicationModel)]
        self.classifier = None
        self.positiveSampleWeight = 0.25
    
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

    def outputGraph(self, author_set, outfile):
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
                if self.classify(authors[i],authors[j]):
                    print(nocomma([authors[i].pk,authors[j].pk]), file=outfile)



