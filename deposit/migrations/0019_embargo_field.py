# Generated by Django 4.2.4 on 2019-10-10 11:56

from django.db import migrations, models

def add_publication_date_when_published(apps, schema_editor):
    """
    If a DepositRecord has status ``published``, set ``publication_date`` to ``date``
    """
    DepositRecord = apps.get_model('deposit', 'DepositRecord')

    qs = DepositRecord.objects.filter(status='published', pub_date__isnull=True)

    for d in qs:
        d.pub_date = d.date.date()

    DepositRecord.objects.bulk_update(qs, ['pub_date'], 1000)


def do_nothing(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('deposit', '0018_letter_of_declaration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='depositrecord',
            name='status',
            field=models.CharField(choices=[('failed', 'Failed'), ('faked', 'Faked'), ('pending', 'Pending publication'), ('embargoed', 'Embargo'), ('published', 'Published'), ('refused', 'Refused by the repository'), ('deleted', 'Deleted')], max_length=64),
        ),
        migrations.AddField(
            model_name='depositrecord',
            name='pub_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='repository',
            name='embargo',
            field=models.CharField(choices=[('none', 'None'), ('optional', 'Optional'), ('required', 'Required')], default='none', max_length=24),
        ),
        migrations.AlterField(
            model_name='depositrecord',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.RunPython(add_publication_date_when_published, do_nothing),
    ]
