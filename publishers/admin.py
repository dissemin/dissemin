# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from publishers.models import *


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


class JournalAdmin(admin.ModelAdmin):
    raw_id_fields = ('stats', 'publisher')
    list_display = ('title', 'issn', 'publisher')


class PublisherAdmin(admin.ModelAdmin):
    raw_id_fields = ('stats',)
    list_display = ('name', 'oa_status')

admin.site.register(Journal, JournalAdmin)
admin.site.register(Publisher, PublisherAdmin)
