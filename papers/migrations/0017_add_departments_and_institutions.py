# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial'),
        ('papers', '0016_cleaner_doctypes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('stats', models.ForeignKey(blank=True, to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='department',
            name='institution',
            field=models.ForeignKey(to='papers.Institution', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='department',
            name='stats',
            field=models.ForeignKey(blank=True, to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='researcher',
            name='department',
            field=models.ForeignKey(to='papers.Department', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
