# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0011_researcher_fetch_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='empty_orcid_profile',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='researcher',
            name='current_task',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[('init', 'Preparing profile'), ('orcid', 'Fetching publications from ORCID'), ('crossref', 'Fetching publications from CrossRef'), ('base', 'Fetching publications from BASE'), ('core', 'Fetching publications from CORE'), ('oai', 'Fetching publications from OAI-PMH'), ('clustering', 'Clustering publications'), ('stats', 'Updating statistics')]),
        ),
    ]
