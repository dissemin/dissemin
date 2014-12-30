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

from papers.models import *

out = open('learning/dataset/author_ids', 'w')

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

def sample2(lst, nb_samples):
    return sample(lst, min(len(lst), nb_samples))

for researcher in Researcher.objects.filter(department_id=21):
    authors = Author.objects.filter(researcher=researcher,paper__year__gt=2012)
    authors_valid = list(authors.filter(paper__visibility='VISIBLE'))
    authors_invalid = list(authors.filter(paper__visibility='DELETED'))
    nb_valid = len(authors_valid)
    nb_invalid = len(authors_invalid)
    indices_valid = sample2(indices_same_set(nb_valid), 2*nb_valid)
    indices_invalid = sample2(indices_two_sets(nb_valid, nb_invalid), 2*(nb_invalid+nb_valid))

    for (i,j) in indices_valid:
        # Generate positive training examples
        print('\t'.join([str(authors_valid[i].pk),str(authors_valid[j].pk),'1']), file=out)

    for (i,j) in indices_invalid:
        # Generate negative training examples
        print('\t'.join([str(authors_valid[i].pk),str(authors_invalid[j].pk),'0']), file=out)

#for p in Paper.objects.filter(author__name__researcher__department_id=24,year__gt=2012):
#    visible = 0
#    if p.visibility == 'VISIBLE':
#        visible = 1
#    elif p.visibility == 'CANDIDATE':
#        continue
#    print(str(p.pk)+"\t"+str(visible),file=out)

out.close()



