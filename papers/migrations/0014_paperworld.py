# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial'),
        ('papers', '0013_researchers_have_users'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperWorld',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stats', models.ForeignKey(to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Paper World',
            },
            bases=(models.Model,),
        ),
    ]
