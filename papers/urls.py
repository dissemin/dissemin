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

from django.conf.urls import include, url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

from papers import views, ajax

urlpatterns = [
        url(r'^$', views.index, name='index'),
        # Paper views
        url(r'^search/$', views.PaperSearchView.as_view(), name='search'),
        url(r'^r/(?P<researcher>\d+)/(?P<slug>[\w-]+)?$', views.ResearcherView.as_view(), name='researcher'),
        url(r'^researcher/(?P<researcher>\d+)$', views.ResearcherView.as_view()),  # Deprecated URL
        url(r'^(?P<orcid>[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9])/$', views.ResearcherView.as_view(), name='researcher-by-orcid'),
        url(r'^my-profile', views.myProfileView, name='my-profile'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view()), # Deprecated URL
        url(r'^p/(?P<pk>\d+)/(?P<slug>[\w-]+)?$', views.PaperView.as_view(), name='paper'),
        url(r'^(?P<doi>10\..*)', views.PaperView.as_view(), name='paper-doi'),
        url(r'^mail_paper/(?P<pk>\d+)/$', views.mailPaperView, name='mail_paper'),
        url(r'^journal/(?P<journal>\d+)/$', views.searchView, name='journal'),
        # Institution-specific views
        url(r'^department/(?P<pk>\d+)/$', views.DepartmentView.as_view(), name='department'),
        url(r'^search/department/(?P<pk>\d+)/$', views.DepartmentPapersView.as_view(), name='department-papers'),
        url(r'^institution/(?P<pk>\d+)/$', views.InstitutionView.as_view(), name='institution'),
        # Tasks, AJAX
        url(r'^ajax/', include('papers.ajax')),
        url(r'^researcher/(?P<pk>\d+)/update/$', views.refetchResearcher, name='refetch-researcher'),
        url(r'^researcher/(?P<pk>\d+)/recluster/$', views.reclusterResearcher, name='recluster-researcher'),
        # API
        url(r'^api/', include('papers.api')),
        # Annotations (to be deleted)
        url(r'^annotations/$', views.AnnotationsView.as_view(), name='annotations'),
]
