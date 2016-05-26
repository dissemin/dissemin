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
import cPickle
import numpy as np
from unidecode import unidecode
import name_tools
from django.core.exceptions import ObjectDoesNotExist

from papers.models import Name, Author, Researcher
from papers.utils import iunaccent, nocomma, filter_punctuation, tokenize
from papers.name import match_names, name_similarity, to_plain_name

class AuthorNotFound(Exception):
    def __init__(self, message, pk, *args):
        self.message = message
        self.pk = pk
        super(AuthorNotFound, self).__init__(message, *args)

class SimilarityFeature(object):
    """
    A feature for a binary classifier: given two authors,
    do they represent the same person?
    """
    def __init__(self):
        """
        Parameters should be set here.
        """
        pass

    def fetchData(self, author):
        """
        Fetches the data used by the classifier from the Author object
        """
        return None

    def score(self, dataA, dataB):
        """
        Computes the score based on the two data returned by fetchData.
        This function should be as simple as possible, expensive computations
        should be kept in fetchData if possible
        """
        return 0.

    def compute(self, authorA, authorB):
        """
        Fetches data for the authors and computes the similarity
        WARNING: recomputing the classifying data every time might be expensive.
        Ideally, this method should not be reimplemented.
        """
        return self.score(self.fetchData(authorA), self.fetchData(authorB))


class AuthorNameSimilarity(SimilarityFeature):
    """
    Similarity of the names of the target authors.
    This is kept separate from CoauthorsSimilarity as it is probably
    useful to give it a different weight in the classifier.
    """
    def __init__(self):
        super(AuthorNameSimilarity, self).__init__()

    def fetchData(self, author):
        return to_plain_name(author.name)

    def score(self, dataA, dataB):
        # TODO: this score function is far from optimal
        # refine it so that 'Claire Mathieu' and 'Claire Mathieu-Kenyon' gets
        # a decent score
        firstA, lastA = dataA
        firstB, lastB = dataB
        return name_similarity(dataA,dataB)

class CoauthorsSimilarity(SimilarityFeature):
    """
    Number of matching coauthors (without the target authors themselves)
    """
    def __init__(self):
        super(CoauthorsSimilarity, self).__init__()
        self.max_nb_authors = 32
    
    def fetchData(self, author):
        if author.paper.author_count > self.max_nb_authors:
            return None
        coauthors = author.paper.author_set.exclude(id=author.id).select_related('name')
        return map(lambda author: (author.name.first,author.name.last), coauthors)

    def score(self, dataA, dataB):
        score = 0.
        if dataA is None or dataB is None:
            return 0.
        for a in dataA:
            for b in dataB:
                firstA, lastA = a
                firstB, lastB = b
                score += name_similarity(a,b)
                #score += name_tools.match(firstA+' '+lastA,firstB+' '+lastB)
                # Previously, it was:
                #if match_names(a,b):
                #    score += 1.
        return score

class NameLengths(SimilarityFeature):
    """
    Length of the last name (if common)
    """
    def __init__(self):
        super(NameLengths, self).__init__()

    def fetchData(self, author):
        return author.name.last

    def score(self, dataA, dataB):
        if dataA.lower() != dataB.lower():
            return 0
        else:
            return len(dataA)

class NumberOfAuthorsSimilarity(SimilarityFeature):
    """
    Similarity of the number of authors of the two papers
    """
    def __init__(self):
        super(NumberOfAuthorsSimilarity, self).__init__()

    def fetchData(self, author):
        return author.paper.author_count

    def score(self, dataA, dataB):
        return (-1.)*pow(dataA-dataB, 2)/(dataA+dataB+1)

def intersectionScore(model, wordsA, wordsB, explain=False):
    """
    Returns the sum of the -log scores of the common words in the two sets
    """
    threshold = 4 # TODO this threshold should depend on the language model used.
    intersection = wordsA & wordsB
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

    def fetchData(self, author):
        return set(filter_punctuation(tokenize(author.paper.title)))

    def score(self, dataA, dataB):
        return intersectionScore(self.languageModel, dataA, dataB)

class ContributorsSimilarity(SimilarityFeature):
    """
    Similarity between the contributors (institutions according to HAL)
    """
    def __init__(self, languageModel):
        super(ContributorsSimilarity, self).__init__()
        self.languageModel = languageModel

    def fetchData(self, author):
        contributors = [r.contributors for r in author.paper.oairecord_set.all()]
        contributors = filter(lambda x: x != None, contributors)
        ta = ' '.join(contributors)
        return set(filter_punctuation(tokenize(ta)))

    def score(self, dataA, dataB):
        return intersectionScore(self.languageModel, dataA, dataB)


class PublicationSimilarity(SimilarityFeature):
    """
    Similarity between the publications associated to the two papers.
    The keywords provided through OAI-PMH are also taken into account.
    """
    def __init__(self, languageModel):
        super(PublicationSimilarity, self).__init__()
        self.languageModel = languageModel

    def fetchData(self, author):
        pubs = author.paper.publications[:5]
        titles = [a.full_journal_title() for a in pubs]
        for r in author.paper.oairecords[:5]:
            if r.keywords:
                titles.append(r.keywords)
        titles = map(lambda t: set(filter_punctuation(tokenize(t))), titles)
        return titles

    def score(self, dataA, dataB):
        nbPairs = 0
        totalScore = 0.
        for ta in dataA:
            for tb in dataB:
                nbPairs += 1
                if ta == tb:
                    totalScore += 40.0
                else:
                    totalScore += intersectionScore(self.languageModel, ta, tb)
              
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
                AuthorNameSimilarity(),
                NumberOfAuthorsSimilarity(),
                NameLengths(),
                CoauthorsSimilarity(),
                PublicationSimilarity(publicationModel),
                TitleSimilarity(publicationModel),
                ContributorsSimilarity(contributorsModel),
                ]
        self.publicationModel = publicationModel
        self.contributorsModel = contributorsModel
        self.classifier = None
        self.positiveSampleWeight = 0.1
        self.kernel = 'linear'

    def get_params(self, **kwargs):
        return {
                'languageModel':self.publicationModel,
                'contributorsModel':self.contributorsModel,
                'positiveSampleWeight':self.positiveSampleWeight,
                'kernel':self.kernel}

    def set_params(self, **kwargs):
        if 'kernel' in kwargs:
            self.kernel = kwargs['kernel']
        if 'positiveSampleWeight' in kwargs:
            self.positiveSampleWeight = kwargs['positiveSampleWeight']
        if 'languageModel' in kwargs:
            self.publicationModel = kwargs['languageModel']
        if 'contributorsModel' in kwargs:
            self.contributorsModel = kwargs['contributorsModel']
        return self
    
    def computeFeatures(self, lstDataA, lstDataB):
        if len(lstDataA) != len(self.simFeatures) or len(lstDataB) != len(self.simFeatures):
            return None
        lst = zip(self.simFeatures, lstDataA, lstDataB)
        return map(lambda (f,a,b): f.score(a,b), lst)
        #result = []
        #for (f,a,b) in lst:
        #    print('# Computing feature '+str(type(f)))
        #    result.append(f.score(a,b))
        #return result

    def lstData(self, author):
        return map(lambda f: f.fetchData(author), self.simFeatures)

    def getDataById(self,id):
        try:
            author = Author.objects.get(pk=id)
            return self.lstData(author)
        except Author.DoesNotExist as e:
            raise AuthorNotFound(e.message, id)
 
    def fit(self, features, labels):
        self.classifier = svm.SVC(kernel=str(self.kernel))
        weights = [(self.positiveSampleWeight if label else 1.) for label in labels]
        self.classifier.fit(features, labels, sample_weight=weights)
        return self

    def confusion(self, features, labels):
        if not self.classifier:
            return None
        pred = self.classifier.predict(features)
        return confusion_matrix(pred, labels)

    def classify(self, authorA, authorB):
        """
        Warning: this is inefficient, it might be better to compute the data first
        and then use classifyData
        """
        if not self.classifier:
            return None
        dataA = self.lstData(authorA)
        dataB = self.lstData(authorB)
        return self.classifyData(dataA, dataB)

    def classifyData(self, dataA, dataB, verbose=False):
        feat_vec = self.computeFeatures(dataA, dataB)
        if verbose:
            print(feat_vec)
        output = self.classifier.predict(np.array(feat_vec).reshape(1,-1))
        return output[0]

    def predict(feat_mat):
        """
        Predict labels for raw feature matrix (to be used internally by CV
        grid search)
        """
        return self.classifier.predict(feat_mat)


    def plotClassification(self, features, labels):
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

    def outputGraph(self, author_set, outfile, logf):
        print('nodedef>name VARCHAR,label VARCHAR,pid VARCHAR,visibility VARCHAR', file=outfile)
        author_data = []
        for author in author_set:
            paper = author.paper
            visibility = paper.visibility
            if paper.year <= 2012:
                visibility = 'NOT_LABELLED'
            author_data.append(self.lstData(author))
            print(nocomma([author.pk, unidecode(paper.title), paper.id, visibility]), file=outfile)
        print('edgedef>node1 VARCHAR,node2 VARCHAR', file=outfile)
        authors = list(author_set)
        for i in range(len(authors)):
            for j in range(i):
                output = self.classifyData(author_data[i],author_data[j])
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
 


