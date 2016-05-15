from __future__ import unicode_literals

from django.db import models

from django.conf import settings
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from .serializers import NotificationSerializer
from rest_framework.renderers import JSONRenderer

import json

from .settings import notification_settings

@python_2_unicode_compatible
class Notification(models.Model):
    """
    This model represents a notification on the database.
    """

    payload = JSONField()
    level = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)
    tag = models.CharField(max_length=100, default='')

    def __str__(self):
        return json.dumps(self.payload)

    def serialize_to_json(self):
        serializer = NotificationSerializer(self)
        return JSONRenderer().render(serializer.data)


@python_2_unicode_compatible
class NotificationArchive(models.Model):
    """
    This model holds all the notifications that users received.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    notification = models.ForeignKey(Notification)

    def __str__(self):
        return '[{}] {}'.format(self.user, self.notification)

@python_2_unicode_compatible
class Inbox(models.Model):
    """
    Inbox notifications are stored in this model until users read them.
    Once read, inbox notifications are deleted.
    Moreover, inbox notification have an expire time.
    After that, they'll be automatically removed by Django.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    notification = models.ForeignKey(Notification)

    class Meta:
        verbose_name_plural = _('inboxes')

    def expired(self):
        expiration_date = self.message.date + timezone.timedelta(
                days=notification_settings.INBOX_EXPIRE_DAYS)
        return expiration_date <= timezone.now()

    expired.boolean = True # For the admin interface.

    def __str__(self):
        return '[{}] {}'.format(self.user, self.notification)
