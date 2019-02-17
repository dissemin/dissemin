# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0019_alter_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='pdf_url',
            field=models.URLField(max_length=2048, null=True, blank=True),
        ),
    ]
