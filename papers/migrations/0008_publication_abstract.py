# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0007_rename_identifer_to_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='abstract',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
