from django.contrib import admin
from .models import Inbox, Notification, NotificationArchive

admin.site.register(Inbox)
admin.site.register(Notification)
admin.site.register(NotificationArchive)
