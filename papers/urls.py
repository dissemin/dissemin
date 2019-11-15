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



from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView, TemplateView
from django.conf import settings
from papers import views

urlpatterns = [
    # Paper views
    url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view()),  # Deprecated URL
    url(r'^p/(?P<pk>\d+)/(?P<slug>[\w-]*)$',
        views.PaperView.as_view(), name='paper'),
    url(r'^(?P<doi>10\..*)', views.PaperView.as_view(), name='paper-doi'),
    url(r'^p/direct/(?P<doi>10\..*)', views.redirect_by_doi, name='paper-redirect-doi'),
    # Tasks, AJAX
    url(r'^ajax/', include('papers.ajax')),
    # API
    url(r'^api/', include('papers.api')),
    # robots.txt
    # from https://stackoverflow.com/a/10149452
    url(r'^robots\.txt$', TemplateView.as_view(template_name="robots.txt",
                                               content_type='text/plain')),
    # favicon
    # from https://stackoverflow.com/a/10149452
    url(r'^favicon\.ico$', RedirectView.as_view(
                            url=settings.STATIC_URL + 'favicon/favicon.ico')),
]
