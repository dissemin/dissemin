# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0005_researcher_orcid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='depositrecord',
            name='file',
            field=models.ForeignKey(to='upload.UploadedPDF'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='depositrecord',
            name='upload_type',
            field=models.FileField(upload_to='deposits'),
            preserve_default=True,
        ),
    ]
