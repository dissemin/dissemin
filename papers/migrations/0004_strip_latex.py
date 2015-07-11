# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from papers.utils import unescape_latex


def strip_latex(apps, schema_editor):
    Paper = apps.get_model('papers','Paper')
    size = 100
    cursor = 0
    count = Paper.objects.count()
    while cursor < count:
        papers = Paper.objects.all()[cursor:cursor+size]
        cursor += size
        for paper in papers:
            new_title = unescape_latex(paper.title)
            if new_title != paper.title:
                print '"%s" -> "%s"' % (paper.title,new_title)
                paper.title = new_title
                paper.save(update_fields=['title'])

class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0003_author_position'),
    ]

    operations = [
        migrations.RunPython(strip_latex)
    ]
