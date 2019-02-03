# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def convert_publications(apps, schema_editor):
    OaiRecord = apps.get_model('papers', 'OaiRecord')
    Publication = apps.get_model('papers', 'Publication')

    OaiSource = apps.get_model('papers', 'OaiSource')
    source, _ = OaiSource.objects.get_or_create(identifier='crossref',
            defaults={'name':'Crossref','oa':False,'priority':1,
                'default_pubtype':'journal-article'})

    for p in Publication.objects.all():
        if not p.doi:
            continue
        r = OaiRecord()
        r.identifier = 'oai:crossref.org:'+p.doi
        r.splash_url = 'https://doi.org/'+p.doi
        r.pdf_url = p.pdf_url
        r.description = p.abstract
        r.pubtype = p.pubtype
        r.container = p.container
        r.journal_title = p.title
        r.publisher_name = p.publisher_name
        r.issue = p.issue
        r.volume = p.volume
        r.pages = p.pages
        r.pubdate = p.pubdate
        r.doi = p.doi
        r.publisher_id = p.publisher_id
        r.journal_id = p.journal_id
        r.source_id = source.id
        r.about = p.paper
        r.save()

    Publication.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('publishers', '0002_update_aliases'),
        ('papers', '0023_fingerprint_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='oairecord',
            name='abstract',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='container',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='doi',
            field=models.CharField(max_length=1024, unique=True, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='issue',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='journal',
            field=models.ForeignKey(blank=True, to='publishers.Journal', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='journal_title',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='pages',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='pubdate',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='publisher',
            field=models.ForeignKey(blank=True, to='publishers.Publisher', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='publisher_name',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='oairecord',
            name='volume',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
     #   migrations.RunPython(convert_publications)
    ]


