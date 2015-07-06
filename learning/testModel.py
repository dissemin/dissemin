# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


from __future__ import unicode_literals, print_function
from django.db.models import Q
from papers.models import *
from learning.model import *
from backend.similarity import *

def getAuthorData(sc, id):
    try:
        return author_data_cache[id]
    except KeyError:
        x = sc.getDataById(id)
        author_data_cache[id] = x
        return x


def run():
    # Read dataset
    author_ids = []
    labels = []
    for line in open('learning/dataset/similarity_training_ids', 'r'):
        vals = map(lambda x: int(x), line.strip().split('\t'))
        author_ids.append((vals[0],vals[1]))
        labels.append(vals[2])

    all_papers_model = WordCount()
    all_papers_model.load('models/everything.pkl')
    contributors_model = WordCount()
    contributors_model.load('models/contributors.pkl')
    sc = SimilarityClassifier(languageModel=all_papers_model, contributorsModel=contributors_model)

    author_data_cache = dict()
    recompute = True
    if recompute:
        print("Computing features")
        features = []
        for (idA,idB) in author_ids:
            f = sc.computeFeatures(getAuthorData(sc, idA), getAuthorData(sc, idB))
            features.append(f)
        print("Writing features back")
        outf = open('learning/dataset/author-features', 'w')
        for i in range(len(labels)):
            print('\t'.join(map(lambda x: str(x), features[i])), file=outf)

        outf.close()
    else:
        inf = open('learning/dataset/author-features', 'r')
        features = []
        for line in inf:
            f = map(lambda x: float(x), line.strip().split('\t'))
            features.append(f)
        inf.close()

    if True:
        sc.positiveSampleWeight = 0.04
        sc.train(features, labels, kernel='linear')

        def paper_url(pk):
            print('http://beta.ens.dissem.in/paper/'+str(Author.objects.get(pk=pk).paper_id))

        print("Curious papers")
        pubSc = sc.simFeatures[1]
        for i in range(len(labels)):
            prediction = sc.classifier.predict(features[i])[0]
            if labels[i] == 0 and prediction == 1:
                print("#####")
                paper_url(author_ids[i][0])
                paper_url(author_ids[i][1])
                #print("Explanation")
                #pubSc.compute(Author.objects.get(pk=author_ids[i][0]),
                #        Author.objects.get(pk=author_ids[i][1]), explain=True)

        print(sc.confusion(features, labels))
        #sc.plotClassification(features, labels)
        sc.save('models/similarity.pkl')
    #sc2 = SimilarityClassifier(filename='models/similarity.pkl')
    #print(sc2.confusion(features, labels))

def testResearcher(pk):
    outf = open('learning/dataset/researcher-'+str(pk)+'.gdf', 'w')
    logf = open('learning/dataset/researcher-'+str(pk)+'.log', 'w')
    sc.outputGraph(Author.objects.filter(researcher_id=pk).filter(Q(paper__visibility='VISIBLE') |
        Q(paper__visibility='DELETED')), outf, logf)
    outf.close()
    logf.close()


