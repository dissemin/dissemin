# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='disambiguation',
            name='publications',
        ),
        migrations.RemoveField(
            model_name='disambiguationchoice',
            name='about',
        ),
        migrations.DeleteModel(
            name='Disambiguation',
        ),
        migrations.DeleteModel(
            name='DisambiguationChoice',
        ),
    ]
