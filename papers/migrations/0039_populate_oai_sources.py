# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def populate_oai_sources(apps, schema_editor):
    OaiSource = apps.get_model('papers', 'OaiSource')

    oai_sources = [
        ('arxiv', 'arXiv', False, 10, 'preprint'),
        ('hal', 'HAL', False, 10, 'preprint'),
        ('cairn', 'Cairn', False, 10, 'preprint'),
        ('pmc', 'PubMed Central', False, 10, 'preprint'),
        ('doaj', 'DOAJ', True, 10, 'journal-article'),
        ('persee', 'Persée', True, 10, 'preprint'),
        ('zenodo', 'Zenodo', False, 15, 'preprint'),
        ('numdam', 'Numdam', False, 10, 'journal-article'),
        ('base', 'BASE', False, -2, 'preprint'),
        ('researchgate', 'ResearchGate', False, -10, 'journal-article'),
        ('crossref', 'Crossref', False, 20, 'journal-article'),
        ('orcid', 'ORCID', False, 1, 'other'),
        ]

    # Auto-create all the Oai Sources when this module is imported
    for identifier, name, oa, priority, pubtype in oai_sources:
        OaiSource.objects.get_or_create(
            identifier=identifier,
            defaults={'name': name,
                      'oa': oa,
                      'priority': priority,
                      'default_pubtype': pubtype})

def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0038_add_index_on_last_modified'),
    ]

    operations = [
        migrations.RunPython(populate_oai_sources, do_nothing)
    ]


