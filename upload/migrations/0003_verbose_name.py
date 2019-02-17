# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0002_uploadedpdf_num_pages'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='uploadedpdf',
            options={'verbose_name': 'Uploaded PDF'},
        ),
    ]
