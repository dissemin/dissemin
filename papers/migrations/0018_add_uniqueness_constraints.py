# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0017_add_departments_and_institutions'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='name',
            unique_together=set([('first', 'last')]),
        ),
        migrations.AlterUniqueTogether(
            name='namevariant',
            unique_together=set([('name', 'researcher')]),
        ),
    ]
