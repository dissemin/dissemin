# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict

from django.db import migrations, models

def cleanup_publisher_aliases(apps, schema_editor):
    AliasPublisher = apps.get_model("publishers", "AliasPublisher")
    Publication = apps.get_model("papers", "Publication")
    AliasPublisher.objects.all().delete()
    Publication.objects.filter(journal__isnull=True).update(publisher=None)
    
    counts = defaultdict(int)
    for p in Publication.objects.filter(publisher__isnull=False):
        pair = (p.publisher_name,p.publisher_id)
        counts[pair] += 1

    for (name,pk) in counts:
        alias = AliasPublisher(name=name,publisher_id=pk)
        alias.count = counts[(name,pk)]
        alias.save()


    print "Please run refetch_publishers()"


class Migration(migrations.Migration):

    dependencies = [
        ('publishers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cleanup_publisher_aliases),
    ]
