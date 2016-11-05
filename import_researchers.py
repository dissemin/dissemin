# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from codecs import open

from papers.models import Department
from papers.models import Researcher
from papers.name import normalize_name_words

last_name_f = 0
first_name_f = 1
url_f = 2
email_f = 3
role_f = 4
dept_f = 5


def import_from_tsv(filename):
    f = open(filename, 'r', 'utf-8')

    for line in f:
        fields = line.strip().split('\t')
        print fields

        dept = fields[dept_f]
        (department, found) = Department.objects.get_or_create(name__iexact=dept,
                                                               defaults={'name': dept.strip()})

        email = fields[email_f]
        if email == '':
            email = None

        first = fields[first_name_f]
        last = normalize_name_words(fields[last_name_f])
        homepage = fields[url_f]
        role = fields[role_f]
        if homepage == '':
            homepage = None

        try:
            Researcher.create_from_scratch(
                first, last, department, email, role, homepage)
        except ValueError:
            print "ValueError"
            continue


import_from_tsv('data/cambridge_researchers')
