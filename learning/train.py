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


w = WordCount()
w_contrib = WordCount()
w_journal = WordCount()

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


exit(0)

w = PaperModel()

dpt = dict()
for d in Department.objects.all():
    dpt[d.pk] = PaperModel()

count = 0
for p in Paper.objects.filter(visibility="VISIBLE"):
    if count % 100 == 0:
        print count
    count += 1
    authors = p.author_set.all()

    raw_features = PaperModel.makeRawFeatures(p, authors)
    for author in authors:
        researcher = author.name.researcher
        if researcher:
            dpt[researcher.department_id].feedRawFeatures(raw_features)
    w.feedRawFeatures(raw_features)


w.save('models/all_papers.pkl')
for d in Department.objects.all():
    dpt[d.pk].save('models/dpt-'+str(d.pk)+'.pkl')



