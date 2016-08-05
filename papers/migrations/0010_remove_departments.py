# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0009_empty'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='department',
            name='stats',
        ),
        migrations.RemoveField(
            model_name='researcher',
            name='department',
        ),
        migrations.DeleteModel(
            name='Department',
        ),
        migrations.RemoveField(
            model_name='researcher',
            name='groups',
        ),
        migrations.DeleteModel(
            name='ResearchGroup',
        ),
    ]
