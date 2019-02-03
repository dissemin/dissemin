# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings
from papers import baremodels


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('statistics', '0001_initial'),
        ('publishers', '0001_initial'),
    ]

    operations = [
#        migrations.CreateModel(
#            name='AccessStatistics',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#                ('num_oa', models.IntegerField(default=0)),
#                ('num_ok', models.IntegerField(default=0)),
#                ('num_couldbe', models.IntegerField(default=0)),
#                ('num_unk', models.IntegerField(default=0)),
#                ('num_closed', models.IntegerField(default=0)),
#                ('num_tot', models.IntegerField(default=0)),
#            ],
#            options={
#            },
#            bases=(models.Model,),
#        ),
#        migrations.CreateModel(
#            name='AliasPublisher',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#                ('name', models.CharField(max_length=512)),
#                ('count', models.IntegerField(default=0)),
#            ],
#            options={
#            },
#            bases=(models.Model,),
#        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(max_length=64)),
                ('timestamp', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_children', models.IntegerField(default=1)),
                ('cluster_relevance', models.FloatField(default=0)),
                ('affiliation', models.CharField(max_length=512, null=True, blank=True)),
                ('cluster', models.ForeignKey(related_name='clusterrel', blank=True, to='papers.Author', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,baremodels.BareAuthor),
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('stats', models.ForeignKey(to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Disambiguation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=512)),
                ('issn', models.CharField(max_length=128)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DisambiguationChoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=512)),
                ('issn', models.CharField(max_length=128)),
                ('about', models.ForeignKey(to='papers.Disambiguation', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
#        migrations.CreateModel(
#            name='Journal',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#                ('title', models.CharField(max_length=256, db_index=True)),
#                ('last_updated', models.DateTimeField(auto_now=True)),
#                ('issn', models.CharField(max_length=10, unique=True, null=True, blank=True)),
#            ],
#            options={
#                'ordering': ['title'],
#            },
#            bases=(models.Model,),
#        ),
        migrations.CreateModel(
            name='Name',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first', models.CharField(max_length=256)),
                ('last', models.CharField(max_length=256)),
                ('full', models.CharField(max_length=513, db_index=True)),
                ('best_confidence', models.FloatField(default=0.0)),
            ],
            options={
                'ordering': ['last', 'first'],
            },
            bases=(models.Model,baremodels.BareName),
        ),
        migrations.CreateModel(
            name='NameVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confidence', models.FloatField(default=1.0)),
                ('name', models.ForeignKey(to='papers.Name', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OaiRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(unique=True, max_length=512)),
                ('splash_url', models.URLField(max_length=1024, null=True, blank=True)),
                ('pdf_url', models.URLField(max_length=1024, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.TextField(null=True, blank=True)),
                ('contributors', models.CharField(max_length=4096, null=True, blank=True)),
                ('pubtype', models.CharField(max_length=512, null=True, blank=True)),
                ('priority', models.IntegerField(default=1)),
                ('last_update', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,baremodels.BareOaiRecord),
        ),
        migrations.CreateModel(
            name='OaiSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=300)),
                ('name', models.CharField(max_length=100)),
                ('oa', models.BooleanField(default=False)),
                ('priority', models.IntegerField(default=1)),
                ('default_pubtype', models.CharField(max_length=128)),
                ('last_status_update', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=1024)),
                ('fingerprint', models.CharField(max_length=64)),
                ('date_last_ask', models.DateField(null=True)),
                ('pubdate', models.DateField()),
                ('last_modified', models.DateField(auto_now=True)),
                ('visibility', models.CharField(default='VISIBLE', max_length=32)),
                ('last_annotation', models.CharField(max_length=32, null=True, blank=True)),
                ('doctype', models.CharField(max_length=32, null=True, blank=True)),
                ('oa_status', models.CharField(default='UNK', max_length=32, null=True, blank=True)),
                ('pdf_url', models.URLField(max_length=2048, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,baremodels.BarePaper),
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pubtype', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=512)),
                ('container', models.CharField(max_length=512, null=True, blank=True)),
                ('publisher_name', models.CharField(max_length=512, null=True, blank=True)),
                ('issue', models.CharField(max_length=64, null=True, blank=True)),
                ('volume', models.CharField(max_length=64, null=True, blank=True)),
                ('pages', models.CharField(max_length=64, null=True, blank=True)),
                ('pubdate', models.DateField(null=True, blank=True)),
                ('doi', models.CharField(max_length=1024, unique=True, null=True, blank=True)),
                ('journal', models.ForeignKey(blank=True, to='publishers.Journal', null=True, on_delete=models.CASCADE)),
                ('paper', models.ForeignKey(to='papers.Paper', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
 #       migrations.CreateModel(
 #           name='Publisher',
 #           fields=[
 #               ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
 #               ('romeo_id', models.CharField(max_length=64)),
 #               ('name', models.CharField(max_length=256, db_index=True)),
 #               ('alias', models.CharField(max_length=256, null=True, blank=True)),
 #               ('url', models.URLField(null=True, blank=True)),
 #               ('preprint', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
 #               ('postprint', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
 #               ('pdfversion', models.CharField(default='unknown', max_length=32, choices=[('can', 'Allowed'), ('cannot', 'Forbidden'), ('restricted', 'Restricted'), ('unclear', 'Unclear'), ('unknown', 'Unknown')])),
 #               ('oa_status', models.CharField(default='UNK', max_length=32, choices=[('OA', 'Open access'), ('OK', 'Allows pre/post prints'), ('NOK', 'Forbids pre/post prints'), ('UNK', 'Policy unclear')])),
 #               ('stats', models.ForeignKey(to='statistics.AccessStatistics', null=True)),
 #           ],
 #           options={
 #           },
 #           bases=(models.Model,),
 #       ),
 #       migrations.CreateModel(
 #           name='PublisherCondition',
 #           fields=[
 #               ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
 #               ('text', models.CharField(max_length=1024)),
 #               ('publisher', models.ForeignKey(to='publishers.Publisher')),
 #           ],
 #           options={
 #           },
 #           bases=(models.Model,),
 #       ),
 #       migrations.CreateModel(
 #           name='PublisherCopyrightLink',
 #           fields=[
 #               ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
 #               ('text', models.CharField(max_length=256)),
 #               ('url', models.URLField()),
 #               ('publisher', models.ForeignKey(to='publishers.Publisher')),
 #           ],
 #           options={
 #           },
 #           bases=(models.Model,),
 #       ),
 #       migrations.CreateModel(
 #           name='PublisherRestrictionDetail',
 #           fields=[
 #               ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
 #               ('text', models.CharField(max_length=256)),
 #               ('applies_to', models.CharField(max_length=32)),
 #               ('publisher', models.ForeignKey(to='publishers.Publisher')),
 #           ],
 #           options={
 #           },
 #           bases=(models.Model,),
 #       ),
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('homepage', models.URLField(null=True, blank=True)),
                ('role', models.CharField(max_length=128, null=True, blank=True)),
                ('last_doi_search', models.DateTimeField(null=True, blank=True)),
                ('status', models.CharField(max_length=512, null=True, blank=True)),
                ('last_status_update', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(to='papers.Department', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResearchGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='researcher',
            name='groups',
            field=models.ManyToManyField(to='papers.ResearchGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='researcher',
            name='name',
            field=models.ForeignKey(to='papers.Name', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='researcher',
            name='stats',
            field=models.ForeignKey(to='statistics.AccessStatistics', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='publication',
            name='publisher',
            field=models.ForeignKey(blank=True, to='publishers.Publisher', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='oairecord',
            name='about',
            field=models.ForeignKey(to='papers.Paper', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='oairecord',
            name='source',
            field=models.ForeignKey(to='papers.OaiSource', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='namevariant',
            name='researcher',
            field=models.ForeignKey(to='papers.Researcher', on_delete=models.CASCADE),
            preserve_default=True,
        ),
#        migrations.AddField(
#            model_name='journal',
#            name='publisher',
#            field=models.ForeignKey(to='publishers.Publisher'),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='journal',
#            name='stats',
#            field=models.ForeignKey(to='statistics.AccessStatistics', null=True),
#            preserve_default=True,
#        ),
        migrations.AddField(
            model_name='disambiguation',
            name='publications',
            field=models.ManyToManyField(to='papers.Publication'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='author',
            name='name',
            field=models.ForeignKey(to='papers.Name', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='author',
            name='paper',
            field=models.ForeignKey(to='papers.Paper', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='author',
            name='researcher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='papers.Researcher', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='author',
            name='similar',
            field=models.ForeignKey(related_name='similarrel', blank=True, to='papers.Author', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='annotation',
            name='paper',
            field=models.ForeignKey(to='papers.Paper', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='annotation',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
#        migrations.AddField(
#            model_name='aliaspublisher',
#            name='publisher',
#            field=models.ForeignKey(to='publishers.Publisher'),
#            preserve_default=True,
#        ),
    ]
