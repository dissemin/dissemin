# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from deposit.models import DepositPreferences

from django.forms import ModelForm

class HALDepositPreferences(DepositPreferences):
    on_behalf_on = models.CharField(max_length=128, null=True, blank=True)

class HALDepositPreferencesForm(ModelForm):
    class Meta:
        model = HALDepositPreferences
        fields = ['on_behalf_on']

