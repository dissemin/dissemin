# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0028_migrate_authors'),
    ]

    operations = [
            migrations.DeleteModel('Author'),
    ]
