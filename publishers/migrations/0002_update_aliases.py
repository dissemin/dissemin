# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict

from django.db import migrations

def backwards(apps, schema_editor):
    """
    Migration nullified after squash of papers
    """
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('publishers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backwards, backwards),
    ]
