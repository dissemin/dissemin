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
from time import sleep
from django.db.models import Q

def cleanup_papers():
    """
    Deletes all the papers where none of the authors have been identified
    as a known researcher.
    TODO: write another version focusing on the last name only.
    """
    deleted_count = 0
    for p in Paper.objects.all().select_related('author'):
        sleep(0.1)
        researcher_found = False
        for a in p.author_set.all():
            if a.researcher:
                researcher_found = True
                break
        if not researcher_found:
            print "Deleting paper id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" papers"


def cleanup_researchers():
    """
    Deletes all the researchers who have not authored any paper.
    """
    deleted_count = 0
    for p in Researcher.objects.all():
        nb_papers = Paper.objects.filter(author__researcher=p).count()
        if not nb_papers:
            print "Deleting researcher id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" researchers"


def cleanup_names(dry_run = False):
    """
    Deletes all the names that are not present in any paper.
    """
    deleted_count = 0
    for n in Name.objects.all():
        if not n.researcher:
            nb_papers = Author.objects.filter(name=n).count()
            if not nb_papers:
                print "Deleting name id "+str(n.pk)+": "+unicode(n)
                deleted_count += 1
                if not dry_run:
                    n.delete()
    print "Deleted "+str(deleted_count)+" names"


