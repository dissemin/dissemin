# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


from __future__ import unicode_literals, print_function
from django.db.models import Q
from papers.models import *
from learning.model import *
from papers.similarity import *

# Read dataset
author_ids = []
labels = []
for line in open('learning/dataset/author_ids', 'r'):
    vals = map(lambda x: int(x), line.strip().split('\t'))
    author_ids.append((vals[0],vals[1]))
    labels.append(vals[2])

all_papers_model = WordCount()
all_papers_model.load('models/everything.pkl')
sc = SimilarityClassifier(all_papers_model)

recompute = False
if recompute:
    print("Getting authors")
    authors = sc._toAuthorPairs(author_ids)
    print("Computing features")
    features = sc._toFeaturePairs(authors)
    print("Writing features back")
    outf = open('learning/dataset/author-features', 'w')
    for i in range(len(labels)):
        print('\t'.join([str(features[i][0]), str(features[i][1])]), file=outf)

    outf.close()
else:
    inf = open('learning/dataset/author-features', 'r')
    features = []
    for line in inf:
        f = map(lambda x: float(x), line.strip().split('\t'))
        features.append(f)
    inf.close()

def paper_url(pk):
    print('http://localhost:8000/paper/'+str(Author.objects.get(pk=pk).paper_id))
print("Curious papers")
pubSc = sc.simFeatures[1]
for i in range(len(labels)):
    if features[i][1] > 10.0 and labels[i] == 0:
        print("#####")
        paper_url(author_ids[i][0])
        paper_url(author_ids[i][1])
        print("Explanation")
        pubSc.compute(Author.objects.get(pk=author_ids[i][0]),
                Author.objects.get(pk=author_ids[i][1]), explain=True)

sc.train(features, labels, kernel='linear')
print(sc.confusion(features, labels))
sc.plotClassification(features, labels)

def testResearcher(pk):
    outf = open('learning/dataset/researcher-'+str(pk)+'.gdf', 'w')
    sc.outputGraph(Author.objects.filter(researcher_id=pk).filter(Q(paper__visibility='VISIBLE') |
        Q(paper__visibility='DELETED')), outf)
    outf.close()


#w = WordCount()
#
#for p in Paper.objects.filter(visibility="VISIBLE"):
#    w.feedLine(p.title)
#
#w.save('titles.wc')


