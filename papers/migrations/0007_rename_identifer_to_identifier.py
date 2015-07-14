# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0006_uploadedpdf_instead_of_file_for_depositrecord'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='depositrecord',
            name='identifer',
        ),
        migrations.AddField(
            model_name='depositrecord',
            name='identifier',
            field=models.CharField(max_length=512, null=True, blank=True),
            preserve_default=True,
        ),
    ]
