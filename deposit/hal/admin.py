
from django.contrib import admin

from .models import HALDepositPreferences
from deposit.admin import DepositPreferencesAdmin

class HALDepositPreferencesAdmin(DepositPreferencesAdmin):
    pass

admin.site.register(HALDepositPreferences, HALDepositPreferencesAdmin)
