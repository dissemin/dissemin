# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0018_add_uniqueness_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
