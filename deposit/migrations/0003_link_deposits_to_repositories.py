# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deposit', '0002_repository'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='repository',
            options={'verbose_name_plural': 'Repositories'},
        ),
        migrations.AddField(
            model_name='depositrecord',
            name='repository',
            field=models.ForeignKey(default=0, to='deposit.Repository', on_delete=models.CASCADE),
            preserve_default=False,
        ),
    ]
