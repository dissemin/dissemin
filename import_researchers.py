# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from papers.models import *
from codecs import open

first_name_f = 0
last_name_f = 1
email_f = 2
dept_f = 3

def import_from_tsv(filename):
    f = open(filename, 'r', 'utf-8')

    for line in f:
        fields = line.split('\t')

        dept = fields[dept_f]
        (department, found) = Department.objects.get_or_create(name__iexact=dept,defaults={'name':dept})

        email = fields[email_f]
        if email == '':
            email = None

        n, created = Name.objects.get_or_create(first=fields[first_name_f], last=fields[last_name_f])
        if created:
            r = Researcher(department=department, email=email)
            r.save()
            n.researcher = r
            n.save()

import_from_tsv('data/import.tsv')
