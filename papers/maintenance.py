# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from papers.models import *

def cleanup_papers():
    deleted_count = 0
    for p in Paper.objects.all():
        researcher_found = False
        for a in p.author_set.all():
            if a.name.researcher:
                researcher_found = True
                break
        if not researcher_found:
            print "Deleting paper id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" papers"


def cleanup_researchers():
    deleted_count = 0
    for p in Researcher.objects.all():
        nb_papers = Paper.objects.filter(author__name__researcher=p).count()
        if not nb_papers:
            print "Deleting researcher id "+str(p.pk)
            deleted_count += 1
            p.delete()
    print "Deleted "+str(deleted_count)+" researchers"


def cleanup_names(dry_run = False):
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


