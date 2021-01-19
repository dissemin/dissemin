from django.conf import settings
from django.db import models


class ShibbolethAccount(models.Model):
    """
    Class that is a concordance between Django User model and eduPersonTargetedId (or any other identifier)
    """
    #: The Django User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='shibboleth_account',
        on_delete=models.CASCADE,
    )
    #: eduPersonTargetedId must nox exceed 256 characters according to definition
    shib_username = models.CharField(
        max_length=256,
        unique=True,
    )

    def __str__(self):
        return '{} {}'.format(self.user, self.shib_username)
