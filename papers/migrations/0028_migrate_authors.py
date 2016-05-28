# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def populate_authors(apps, schema_editor):
    Author = apps.get_model('papers', 'Author')
    Name = apps.get_model('papers', 'Name')
    Paper = apps.get_model('papers', 'Paper')

    for p in Paper.objects.all():
        authors = sorted(p.author_set.all().prefetch_related('name'),
                        key=lambda r: r.position)
        authors_list = [a.serialize() for a in authors]
        p.authors_list = authors_list
        p.save(update_fields=['authors_list'])

def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0027_paper_authors_list'),
    ]

    operations = [
        migrations.RunPython(populate_authors, do_nothing)
    ]


