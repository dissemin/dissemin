# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0004_strip_latex'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='orcid',
            field=models.CharField(max_length=32, unique=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
