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

from __future__ import unicode_literals

from django.conf.urls import include
from django.conf.urls import url
from django.views.generic.base import RedirectView, TemplateView
from papers import views
from django.conf import settings

urlpatterns = [
        url(r'^$', views.index, name='index'),
        # Paper views
        url(r'^search/$', views.PaperSearchView.as_view(), name='search'),
        url(r'^r/(?P<researcher>\d+)/(?P<slug>[\w-]*)$',
            views.ResearcherView.as_view(), name='researcher'),
        url(r'^researcher/(?P<researcher>\d+)$',
            views.ResearcherView.as_view()),  # Deprecated URL
        url(r'^(?P<orcid>[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9])/$',
            views.ResearcherView.as_view(), name='researcher-by-orcid'),
        url(r'^my-profile', views.myProfileView, name='my-profile'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view()),  # Deprecated URL
        url(r'^p/(?P<pk>\d+)/(?P<slug>[\w-]*)$',
            views.PaperView.as_view(), name='paper'),
        url(r'^(?P<doi>10\..*)', views.PaperView.as_view(), name='paper-doi'),
        url(r'^search/b/(?P<publisher>\d+)/(?P<slug>[\w-]*)$',
            views.PublisherPapersView.as_view(), name='publisher-papers'),
        url(r'^journal/(?P<journal>\d+)/$',
            views.JournalPapersView.as_view(), name='journal'),
        # Institution-specific views
        url(r'^department/(?P<pk>\d+)/$',
            views.DepartmentView.as_view(), name='department'),
        url(r'^search/department/(?P<pk>\d+)/$',
            views.DepartmentPapersView.as_view(), name='department-papers'),
        url(r'^institution/(?P<pk>\d+)/$',
            views.InstitutionView.as_view()), # Deprecated URL
        url(r'^i/(?P<pk>\d+)/(?P<slug>[\w-]*)$',
            views.InstitutionView.as_view(), name='institution'),
        url(r'^institutions$',
            views.InstitutionsMapView.as_view(), name='institutions-map'),
        # Tasks, AJAX
        url(r'^ajax/', include('papers.ajax')),
        url(r'^researcher/(?P<pk>\d+)/update/$',
            views.refetchResearcher, name='refetch-researcher'),
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
