# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from papers.models import *
from papers.utils import iunaccent
from codecs import open

first_name_f = 1
last_name_f = 0
email_f = 2
url_f = 3
role_f = 4
group_f = 5
dept_f = 6

def import_from_tsv(filename):
    f = open(filename, 'r', 'utf-8')

    for line in f:
        fields = line.strip().split('\t')
        print fields
        print len(fields)

        dept = fields[dept_f]
        (department, found) = Department.objects.get_or_create(name__iexact=dept,
                defaults={'name':dept.strip()})

        email = fields[email_f]
        if email == '':
            email = None

        first = fields[first_name_f]
        last = fields[last_name_f]
        full = iunaccent(first+' '+last)
        n, created = Name.get_or_create(first,last)
        if created or not n.researcher:
            r = Researcher(department=department, email=email)
            r.save()
            n.researcher = r
        n.researcher.email = email
        n.researcher.homepage = fields[url_f]
        n.researcher.role = fields[role_f]
        
        group = fields[group_f]
        if group:
            g, created = ResearchGroup.objects.get_or_create(name=group)
            n.researcher.groups.add(g)

        n.researcher.save()


import_from_tsv('data/chercheurs-di-dc.tsv.csv')
