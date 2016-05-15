from django.dispatch import Signal

inbox_stored = Signal(providing_args=['user', 'notification'])
inbox_deleted = Signal(providing_args=['user', 'notification_id'])
inbox_purged = Signal(providing_args=['user'])
inbox_cleaned = Signal(providing_args=['user', 'tag'])

archive_stored = Signal(providing_args=['user', 'notification'])
