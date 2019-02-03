# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AliasPublisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('count', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'papers_aliaspublisher',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256, db_index=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('issn', models.CharField(max_length=10, unique=True, null=True, blank=True)),
            ],
            options={
                'ordering': ['title'],
                'db_table': 'papers_journal',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('romeo_id', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=256, db_index=True)),
                ('alias', models.CharField(max_length=256, null=True, blank=True)),
                ('url', models.URLField(null=True, blank=True)),
                ('preprint', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
                ('postprint', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
                ('pdfversion', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
                ('oa_status', models.CharField(default='UNK', max_length=32, choices=[('OA', 'Open access'), ('OK', 'Allows pre/post prints'), ('NOK', 'Forbids pre/post prints'), ('UNK', 'Policy unclear')])),
                ('stats', models.ForeignKey(to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'papers_publisher',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublisherCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=1024)),
                ('publisher', models.ForeignKey(to='publishers.Publisher', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'papers_publishercondition',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublisherCopyrightLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=256)),
                ('url', models.URLField()),
                ('publisher', models.ForeignKey(to='publishers.Publisher', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'papers_publishercopyrightlink',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublisherRestrictionDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=256)),
                ('applies_to', models.CharField(max_length=32)),
                ('publisher', models.ForeignKey(to='publishers.Publisher', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'papers_publisherrestrictiondetail',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='journal',
            name='publisher',
            field=models.ForeignKey(to='publishers.Publisher', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='journal',
            name='stats',
            field=models.ForeignKey(to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='aliaspublisher',
            name='publisher',
            field=models.ForeignKey(to='publishers.Publisher', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
