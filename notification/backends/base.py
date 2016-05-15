class NotificationBackend(object):
    def create_message(self, level, payload, date=None):
        """
        Create and return a `Notification` instance.
        Instance types depends on backends implementation.

        :param level: a notification level (could be seen as priority)
        :param payload: a dict payload serializable (depends on implementation detail: JSON / MsgPack / whatever)
        :param date: a date to deliver the notification on (default: now)
        
        :returns: a Notification instance
        """
        raise NotImplementedError

    def inbox_list(self, user):
        """
        Retrieve all the notifications in a `user` inbox.

        :param user: a user instance

        :returns: an iterable containing `Notification` instances
        """
        raise NotImplementedError
    
    def inbox_purge(self, user):
        """
        Delete all the notifications in `user` inbox.

        :param user: a user instance

        :returns: nothing.
        """
        raise NotImplementedError
    
    def inbox_store(self, users, notification):
        """
        Store a `Notification` instance in the inbox for the list of users.

        :param users: an iterable containing users instances.
        :param notification: a notification instance to persist in the inbox

        :raises: MessageTypeNotSupported if `Notification` cannot be managed by the current backend

        :returns: nothing
        """

        raise NotImplementedError

    def inbox_delete(self, user, notification_id):
        """
        Remove a `Notification` instance from user inbox.

        :param user: a user instance
        :param notification_id: a notification identifier

        :returns: None
        """

        raise NotImplementedError
    
    def inbox_get(self, user, notification_id):
        """
        Get a `Notification` from a user inbox.

        :param user: a user instance
        :param notification_id: a notification identifier

        :returns: a notification instance

        :raises: MessageDoesNotExists if notification_id is not found
        """
        raise NotImplementedError

    def archive_store(self, users, notification):
        """
        Store a Notification instance in the archive for a list of users.

        :param users: an iterable containg user instances
        :param notification: Notification instance to persist in archive

        :returns: None
        :raises: MessageTypeNotSupported if notification cannot be managed by current backend
        """
        raise NotImplementedError

    def archive_list(self, user):
        """
        Retrieve all the messages in user archive

        :param user: a user

        :returns: an iterable containing notification
        """
        raise NotImplementedError

    def can_handle(self, notification):
        """
        Determine if this backend can handle this notification

        :param notification: Notification instance
        :returns: True if can handle, False otherwise
        """
        raise NotImplementedError
