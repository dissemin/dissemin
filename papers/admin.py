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
from solo.admin import SingletonModelAdmin
from django_admin_relation_links import AdminChangeLinksMixin

from django.contrib import admin
from django.core.paginator import Paginator
from django.db import connection, transaction, OperationalError
from django.utils.functional import cached_property

from papers.models import Department
from papers.models import Institution
from papers.models import Name
from papers.models import OaiRecord
from papers.models import OaiSource
from papers.models import Paper
from papers.models import PaperWorld
from papers.models import Researcher


class TimeLimitedPaginator(Paginator):
    """
    Paginator that enforced a timeout on the count operation.
    When the timeout is reached a "fake" large value is returned instead,
    Why does this hack exist? On every admin list view, Django issues a
    COUNT on the full queryset. There is no simple workaround. On big tables,
    this COUNT is extremely slow and makes things unbearable. This solution
    is what we came up with.

    Taken from: https://gist.github.com/hakib/5cbda96c8121299088115a94ec634903
    """

    @cached_property
    def count(self):
        # We set the timeout in a db transaction to prevent it from
        # affecting other transactions.
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET LOCAL statement_timeout TO 400;')
            try:
                return super().count
            except OperationalError:
                return 9999999999


class NameInline(admin.TabularInline):
    model = Name
    extra = 0


class OaiInline(admin.TabularInline):
    model = OaiRecord
    extra = 0
    fields = ('identifier', 'source', 'splash_url', 'pdf_url', )


class DepartmentAdmin(admin.ModelAdmin):
    raw_id_fields = ('institution', 'stats', )


class OaiRecordAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    paginator = TimeLimitedPaginator
    search_fields = ('identifier', 'pk', )
    raw_id_fields = ('about', 'journal', 'publisher', )
    readonly_fields = ('last_update', )
    show_full_result_count = False


class PaperAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    changelist_links = [
        (
            'oairecords',
            {
                'lookup_filter' : 'about',
            },
        ),
    ]
    list_display = ('title', 'pubdate', 'visible', 'doctype', 'oa_status')
    paginator = TimeLimitedPaginator
    raw_id_fields = ('todolist', )
    readonly_fields = ('last_modified', )
    search_fields = ('pk', )
    show_full_result_count = False


class PaperWorldAdmin(admin.ModelAdmin):
    raw_id_fields = ('stats', )


class ResearcherAdmin(admin.ModelAdmin):
    list_display = ('name', 'orcid', )
    raw_id_fields = ('department', 'institution', 'name', 'user', 'stats', )
    search_fields = ('user', 'orcid', )


admin.site.register(Institution)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Researcher, ResearcherAdmin)
admin.site.register(Name)
admin.site.register(Paper, PaperAdmin)
admin.site.register(OaiSource)
admin.site.register(OaiRecord, OaiRecordAdmin)
admin.site.register(PaperWorld, SingletonModelAdmin)
