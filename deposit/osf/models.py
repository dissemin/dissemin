# -*- encoding: utf-8 -*-



from django.db import models
from django.utils.translation import ugettext_lazy as _
from deposit.models import DepositPreferences

class OSFDepositPreferences(DepositPreferences):
    on_behalf_of = models.CharField(max_length=128,
                null=True,
                blank=True,
                verbose_name=_('OSF identifier'),
                help_text=_('If set, your deposits will be associated to this OSF account. This identifier is a string of letters and numbers which can be found in your OSF public profile URL.'))


