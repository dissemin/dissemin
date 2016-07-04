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
        r = OaiRecord(source=source)
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

def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0024_publication_to_oairecord'),
    ]

    operations = [
        migrations.RunPython(convert_publications, do_nothing)
    ]


