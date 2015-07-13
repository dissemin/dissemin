# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedpdf',
            name='num_pages',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
