# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0028_migrate_authors'),
    ]

    operations = [
            migrations.DeleteModel('Author'),
    ]
