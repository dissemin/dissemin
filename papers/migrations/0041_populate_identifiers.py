# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from papers.utils import validate_orcid
from bulk_update.helper import bulk_update
from collections import defaultdict

def populate_identifiers(apps, schema_editor):
    Paper = apps.get_model('papers', 'Paper')
    OaiRecord = apps.get_model('papers', 'OaiRecord')

    lastpk = 100000
    bs = 500
    found = True
    while found:
        found = False
        print lastpk
    
        papers = list(Paper.objects.filter(pk__gt=lastpk).order_by('id')[:bs])
        if not papers:
            break
        found = True

        new_lastpk = papers[-1].pk
        records_list = OaiRecord.objects.filter(about_id__gt=lastpk,
                about_id__lte=new_lastpk).values('about_id','identifier','doi')
        records = defaultdict(list)
        for pid, identifier, doi in records_list:
            records[pid].append((identifier, doi))
        
        updated = []
        for p in papers:#.select_related('oairecords'):
            identifiers = set([p.fingerprint])
            for identifier, doi in records[p.id]:
                identifiers.add(identifier)
                if doi:
                    identifiers.add(doi)
            p.identifiers = list(identifiers)
            updated.append(p)
        bulk_update(updated, update_fields=['identifiers'])
        lastpk = new_lastpk

def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    atomic = False

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


