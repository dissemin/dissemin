# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as __
from deposit.models import DepositPreferences


class HALDepositPreferences(DepositPreferences):
    on_behalf_on = models.CharField(max_length=128,
                null=True,
                blank=True,
                verbose_name=__('HAL username'),
                help_text=__('Deposits will be associated to this HAL account'))


