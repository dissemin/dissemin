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


from __future__ import print_function
from random import randint, sample

import datetime
from papers.models import *

out_sim = open('learning/dataset/similarity_training_ids', 'w')
out_rel = open('learning/dataset/relevance_training_ids', 'w')

# Helpers to pick some pairs in identical or different sets
def indices_same_set(n):
    r = []
    for i in range(n):
        for j in range(i):
            r.append((i,j))
    return r

def indices_two_sets(n,p):
    r = []
    for i in range(n):
        for j in range(p):
            r.append((i,j))
    return r

# Sample k elements from a set (ensuring that k does not exceed the cardinal of the set)
def sample2(lst, nb_samples):
    return sample(lst, min(len(lst), nb_samples))

department_id = 21 # informatique

for researcher in Researcher.objects.filter(department_id=department_id):
    authors = Author.objects.filter(name=researcher.name_id,paper__pubdate__gt=datetime.date(2012,01,01))
    authors_valid = list(authors.filter(paper__visibility='VISIBLE'))
    authors_invalid = list(authors.filter(paper__visibility='DELETED'))
    nb_valid = len(authors_valid)
    nb_invalid = len(authors_invalid)

    # Generate similarity training examples
    indices_valid = sample2(indices_same_set(nb_valid), 2*nb_valid)
    indices_invalid = sample2(indices_two_sets(nb_valid, nb_invalid), 2*(nb_invalid+nb_valid))

    #   Positive
    for (i,j) in indices_valid:
        print('\t'.join([str(authors_valid[i].pk),str(authors_valid[j].pk),'1']), file=out_sim)

    #   Negative
    for (i,j) in indices_invalid:
        print('\t'.join([str(authors_valid[i].pk),str(authors_invalid[j].pk),'0']), file=out_sim)

    # Generate relevance training examples
    #   Positive
    for a in authors_valid:
        print('\t'.join([str(a.pk),str(department_id),'1']), file=out_rel)

    #   Negative
    for a in authors_invalid:
        print('\t'.join([str(a.pk),str(department_id),'0']), file=out_rel)


#for p in Paper.objects.filter(author__name__researcher__department_id=24,year__gt=2012):
#    visible = 0
#    if p.visibility == 'VISIBLE':
#        visible = 1
#    elif p.visibility == 'CANDIDATE':
#        continue
#    print(str(p.pk)+"\t"+str(visible),file=out)

out_sim.close()
out_rel.close()



