# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0014_paperworld'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='oairecord',
            options={'verbose_name': 'OAI record'},
        ),
        migrations.AlterModelOptions(
            name='oaisource',
            options={'verbose_name': 'OAI source'},
        ),
        migrations.AddField(
            model_name='paper',
            name='task',
            field=models.CharField(max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='oaisource',
            name='identifier',
            field=models.CharField(unique=True, max_length=300),
            preserve_default=True,
        ),
    ]
