# Generated by Django 2.1.7 on 2019-05-12 17:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('papers', '0055_remove_namevariant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paper',
            name='date_last_ask',
        ),
        migrations.RemoveField(
            model_name='paper',
            name='last_annotation',
        ),
    ]