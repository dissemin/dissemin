# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0015_add_paper_task'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oairecord',
            name='pubtype',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[('journal-article', 'Journal article'), ('proceedings-article', 'Proceedings article'), ('book-chapter', 'Book chapter'), ('book', 'Book'), ('journal-issue', 'Journal issue'), ('proceedings', 'Proceedings'), ('reference-entry', 'Entry'), ('poster', 'Poster'), ('report', 'Report'), ('thesis', 'Thesis'), ('dataset', 'Dataset'), ('preprint', 'Preprint'), ('other', 'Other document')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='oaisource',
            name='default_pubtype',
            field=models.CharField(max_length=64, choices=[('journal-article', 'Journal article'), ('proceedings-article', 'Proceedings article'), ('book-chapter', 'Book chapter'), ('book', 'Book'), ('journal-issue', 'Journal issue'), ('proceedings', 'Proceedings'), ('reference-entry', 'Entry'), ('poster', 'Poster'), ('report', 'Report'), ('thesis', 'Thesis'), ('dataset', 'Dataset'), ('preprint', 'Preprint'), ('other', 'Other document')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='paper',
            name='doctype',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[('journal-article', 'Journal article'), ('proceedings-article', 'Proceedings article'), ('book-chapter', 'Book chapter'), ('book', 'Book'), ('journal-issue', 'Journal issue'), ('proceedings', 'Proceedings'), ('reference-entry', 'Entry'), ('poster', 'Poster'), ('report', 'Report'), ('thesis', 'Thesis'), ('dataset', 'Dataset'), ('preprint', 'Preprint'), ('other', 'Other document')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='publication',
            name='pubtype',
            field=models.CharField(max_length=64, choices=[('journal-article', 'Journal article'), ('proceedings-article', 'Proceedings article'), ('book-chapter', 'Book chapter'), ('book', 'Book'), ('journal-issue', 'Journal issue'), ('proceedings', 'Proceedings'), ('reference-entry', 'Entry'), ('poster', 'Poster'), ('report', 'Report'), ('thesis', 'Thesis'), ('dataset', 'Dataset'), ('preprint', 'Preprint'), ('other', 'Other document')]),
            preserve_default=True,
        ),
    ]
