# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#



from deposit.models import DDC
from deposit.models import DepositRecord
from deposit.models import LicenseChooser
from deposit.models import License
from deposit.models import GreenOpenAccessService
from deposit.models import Repository
from deposit.forms import RepositoryAdminForm
from django.contrib import admin


class LicenseChooserInline(admin.TabularInline):
    model = LicenseChooser
    ordering = ('position', )
    extra = 1

class DepositRecordAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'paper', 'user')
    list_filter = ['repository']
    raw_id_fields = ('paper', 'user', 'oairecord', 'file', )
    readonly_fields = ('date', )
    search_fields = ('paper__pk', 'paper__title')

class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'uri')
    search_fields = ('name', 'uri', 'licensechooser__transmit_id')

class RepositoryAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': [field.name for field in Repository._meta.fields if field.name not in ['id', 'ddc']]
        }),
        ('Classification', {
            'classes': ('collapse',),
            'fields': ('ddc',),
        }),
    )
    filter_horizontal = ('ddc', )
    form = RepositoryAdminForm
    inlines = (LicenseChooserInline, )

admin.site.register(DDC)
admin.site.register(DepositRecord, DepositRecordAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(GreenOpenAccessService)
admin.site.register(Repository, RepositoryAdmin)
