# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0021_change_department_field_on_researcher'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='department',
            field=models.ForeignKey(to='papers.Department', null=True, on_delete=models.CASCADE),
        ),
    ]
