# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from papers.utils import validate_orcid

def populate_identifiers(apps, schema_editor):
    Paper = apps.get_model('papers', 'Paper')

    for p in Paper.objects.all():
        identifiers = set([p.fingerprint])
        for r in p.oairecord_set.all():
            identifiers.add(r.identifier)
            if r.doi:
                identifiers.add(r.doi)
        p.identifiers = list(identifiers)
        p.save(update_fields=['identifiers'])

def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0040_paper_identifiers'),
    ]

    operations = [
        migrations.RunPython(populate_identifiers, do_nothing),
        migrations.RunSQL("""
CREATE INDEX gin_idx_identifiers ON
papers_paper USING gin (identifiers)
WITH (fastupdate = on);
""","""
DROP INDEX IF EXISTS gin_dix_identifiers;
"""),
    ]


