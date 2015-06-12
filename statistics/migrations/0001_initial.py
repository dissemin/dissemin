# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessStatistics',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_oa', models.IntegerField(default=0)),
                ('num_ok', models.IntegerField(default=0)),
                ('num_couldbe', models.IntegerField(default=0)),
                ('num_unk', models.IntegerField(default=0)),
                ('num_closed', models.IntegerField(default=0)),
                ('num_tot', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'papers_accessstatistics',
            },
            bases=(models.Model,),
        ),
    ]
