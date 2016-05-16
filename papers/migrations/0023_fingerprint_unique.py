# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0022_department'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paper',
            name='fingerprint',
            field=models.CharField(unique=True, max_length=64),
        ),
    ]
