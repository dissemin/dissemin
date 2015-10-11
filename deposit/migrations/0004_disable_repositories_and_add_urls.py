# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deposit', '0003_link_deposits_to_repositories'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='url',
            field=models.URLField(max_length=256, null=True, blank=True),
        ),
    ]
