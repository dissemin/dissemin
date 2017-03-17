from django.contrib import admin

from .models import Inbox
from .models import Notification
from .models import NotificationArchive

admin.site.register(Inbox)
admin.site.register(Notification)
admin.site.register(NotificationArchive)
