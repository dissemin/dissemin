# -*- coding: utf-8 -*-


from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0002_notification_tag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='payload',
            field=jsonfield.fields.JSONField(),
        ),
    ]
