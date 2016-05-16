# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0020_publication_pdf_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='papers.Department', null=True),
        ),
    ]
