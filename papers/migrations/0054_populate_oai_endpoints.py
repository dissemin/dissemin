# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

oai_sources = {
    'arxiv':'http://export.arxiv.org/oai2',
    'hal':'https://api.archives-ouvertes.fr/oai/hal/',
    'pmc':'https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi',
    }


def populate_oai_endpoints(apps, schema_editor):
    OaiSource = apps.get_model('papers', 'OaiSource')

    for identifier, endpoint in oai_sources.items():
        OaiSource.objects.filter(identifier=identifier).update(endpoint=endpoint)

def do_nothing(apps, schema_editor):
    OaiSource = apps.get_model('papers', 'OaiSource')

    for identifier, endpoint in oai_sources.items():
        OaiSource.objects.filter(identifier=identifier).update(endpoint=None)


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0053_add_endpoint_to_oai_sources'),
    ]

    operations = [
        migrations.RunPython(populate_oai_endpoints, do_nothing)
    ]


