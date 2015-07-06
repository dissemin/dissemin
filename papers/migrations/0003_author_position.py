# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def prefill_authors(apps, schema_editor):
    Author = apps.get_model('papers','Author')
    Paper = apps.get_model('papers','Paper')
    size = 100
    cursor = 0
    count = Paper.objects.count()
    while cursor < count:
        papers = Paper.objects.all()[cursor:cursor+size]
        cursor += size
        for paper in papers:
            for idx, author in enumerate(paper.author_set.all().order_by('pk')):
                author.position = idx
                author.save(update_fields=['position'])

class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0002_remove_disambiguation_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='position',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.RunPython(prefill_authors)
    ]
