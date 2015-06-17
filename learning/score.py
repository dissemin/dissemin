# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
from __future__ import unicode_literals, print_function

from papers.models import *
from papers.relevance import RelevanceClassifier

# Load dev dataset
samples = []
for line in open('learning/dataset/relevance_training_ids', 'r'):
    vals = map(lambda x: int(x), line.strip().split('\t'))
    samples.append((vals[0],vals[1],vals[2]))

# Retrieve decisions
def get_decision(author_id):
    a = Author.objects.get(pk=author_id)
    return (1 if a.researcher != None else 0)

decisions = []
confusion_matrix = [[0,0],[0,0]]

print()
print("####\n## Similarity + relevance:\n####")
print()

for author_id, dept_id, status in samples:
    dec = get_decision(author_id)
    decisions.append(dec)
    confusion_matrix[status][dec] += 1

# Output statistics
def statistics():
    print(confusion_matrix)

    if len(decisions):
        precision = float(confusion_matrix[1][1])/(confusion_matrix[0][1]+confusion_matrix[1][1])
        recall = float(confusion_matrix[1][1])/(confusion_matrix[1][0]+confusion_matrix[1][1])

        fscore = 2*(precision*recall)/(precision+recall)
        
        print("Precision: "+str(precision))
        print("Recall: "+str(recall))
        print("F-score: "+str(fscore))

statistics()

# Scores for relevance-based classifier
print()
print("####\n## Relevance only:\n####")
print()

relevance_model_fname = 'models/relevance-0.pkl'
rc = RelevanceClassifier(filename=relevance_model_fname)

decisions = []
confusion_matrix = [[0,0],[0,0]]

for author_id, dept_id, status in samples:
    a = Author.objects.get(pk=author_id)
    dst = rc.score(a, dept_id)
    dec = (1 if dst > 0 else 0)
    decisions.append(dec)
    confusion_matrix[status][dec] += 1

statistics()

