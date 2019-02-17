# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0010_remove_departments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='researcher',
            old_name='status',
            new_name='harvester',
        ),
        migrations.RenameField(
            model_name='researcher',
            old_name='last_doi_search',
            new_name='last_harvest',
        ),
        migrations.RemoveField(
            model_name='researcher',
            name='last_status_update',
        ),
        migrations.AddField(
            model_name='researcher',
            name='current_task',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[('orcid', 'Fetching publications from ORCID'), ('crossref', 'Fetching publications from CrossRef'), ('base', 'Fetching publications from BASE'), ('core', 'Fetching publications from CORE'), ('oai', 'Fetching publications from OAI-PMH'), ('clustering', 'Clustering publications'), ('stats', 'Updating statistics')]),
        ),
        migrations.AlterField(
            model_name='researcher',
            name='email',
            field=models.EmailField(max_length=254, null=True, blank=True),
        ),
    ]
