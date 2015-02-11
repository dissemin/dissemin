# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from django.contrib import admin
from papers.models import *

class NameInline(admin.TabularInline):
    model = Name
    extra = 0

class ResearcherAdmin(admin.ModelAdmin):
    fieldsets = [
      #  (None, {'fields': ['nae']}),
        ('Affiliation', {'fields': ['department', 'groups']})
        ]

class AuthorInline(admin.TabularInline):
    model = Author
    extra = 0
    raw_id_fields = ('paper','name')

class OaiInline(admin.TabularInline):
    model = OaiRecord
    extra = 0

class PublicationInline(admin.StackedInline):
    model = Publication
    extra = 0

class PaperAdmin(admin.ModelAdmin):
    fields = ['title', 'pubdate', 'visibility']
    inlines = [AuthorInline, PublicationInline, OaiInline]

admin.site.register(Department)
admin.site.register(ResearchGroup)
admin.site.register(Researcher, ResearcherAdmin)
admin.site.register(Name)
admin.site.register(Paper, PaperAdmin)
admin.site.register(OaiSource)
admin.site.register(OaiRecord)
admin.site.register(Journal)
admin.site.register(Publisher)

