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
from random import randint

from papers.models import *

out = open('learning/dataset/author_ids', 'w')

for researcher in Researcher.objects.filter(department_id=21):
    authors = Author.objects.filter(researcher=researcher,paper__year__gt=2012)
    authors_valid = list(authors.filter(paper__visibility='VISIBLE'))
    authors_invalid = list(authors.filter(paper__visibility='DELETED'))
    nb_valid = len(authors_valid)
    nb_invalid = len(authors_invalid)
    for a in authors_valid:
        # Generate positive training examples
        for k in range(1):
            a2 = authors_valid[randint(0,nb_valid-1)]
            print('\t'.join([str(a.pk),str(a2.pk),'1']), file=out)
        # Generate negative training examples
        if nb_invalid:
            a3 = authors_invalid[randint(0,nb_invalid-1)]
            print('\t'.join([str(a.pk),str(a3.pk),'0']), file=out)
    for a in authors_invalid:
        # Generate negative training examples
        if nb_valid:
            a2 = authors_valid[randint(0,nb_valid-1)]
            print('\t'.join([str(a.pk),str(a2.pk),'0']), file=out)

#for p in Paper.objects.filter(author__name__researcher__department_id=24,year__gt=2012):
#    visible = 0
#    if p.visibility == 'VISIBLE':
#        visible = 1
#    elif p.visibility == 'CANDIDATE':
#        continue
#    print(str(p.pk)+"\t"+str(visible),file=out)

out.close()



