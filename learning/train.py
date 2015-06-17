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


from __future__ import unicode_literals

from papers.models import *
from learning.model import *
from backend.similarity import *

TRAIN_LM = False
TRAIN_SIMILARITY = False

w = WordCount()
w_contrib = WordCount()
w_journal = WordCount()

if TRAIN_LM:
    count = 0
    for p in OaiRecord.objects.filter(about__visibility="VISIBLE"):
        if count % 100 == 0:
            print count
        count += 1
        if p.description and len(p.description) > 50:
            w.feedLine(p.description)
        if p.keywords:
            w.feedLine(p.keywords)
        if p.contributors:
            w_contrib.feedLine(p.contributors)
            
    count = 0
    for p in Publication.objects.filter(paper__visibility="VISIBLE"):
        if count % 100 == 0:
            print count
        count += 1
        w.feedLine(p.full_title())
        w.feedLine(p.paper.title)
        w_journal.feedLine(p.full_title())

    w.save('models/everything.pkl')
    w_contrib.save('models/contributors.pkl')
    w_journal.save('models/publications.pkl')
else:
    w.load('models/everything.pkl')
    w_contrib.load('models/contributors.pkl')
    w_journal.load('models/publications.pkl')

if TRAIN_SIMILARITY:
    sc = SimilarityClassifier(languageModel=w, contributorsModel=w_contrib)
    
    features = []
    labels = []
    dataset = open('learning/dataset/similarity_training_ids', 'r')
    for line in dataset:
        [pid_a, pid_b, lbl] = map(lambda x: int(x), line.strip().split())
        features.append(sc.computeFeatures(sc.getDataById(pid_a), sc.getDataById(pid_b)))
        labels.append(lbl)
    dataset.close()

    sc.train(features, labels)
    sc.save('models/similarity.pkl')

