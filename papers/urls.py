# -*- encoding: utf-8 -*-

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

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

from papers import views, ajax

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^login/$', login, name='login'),
        url(r'^logout/$', views.logoutView, name='logout'),
        url(r'^search/?$', views.searchView, name='search'),
        url(r'^publishers$', views.publishersView, name='publishers'),
        url(r'^researcher/(?P<researcher>\d+)/$', views.searchView, name='researcher'),
        url(r'^researcher/(?P<pk>\d+)/update/$', views.updateResearcher, name='updateResearcher'),
        url(r'^researcher/(?P<pk>\d+)/updateoai/$', views.updateResearcherOAI, name='updateResearcherOAI'),
        url(r'^group/(?P<pk>\d+)/$', views.GroupView.as_view(), name='group'),
        url(r'^department/(?P<pk>\d+)/$', views.DepartmentView.as_view(), name='department'),
        url(r'^departments/$', views.departmentsView, name='departments'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view(), name='paper'),
        url(r'^upload_paper/(?P<pk>\d+)/$', views.UploadPaperView.as_view(), name='upload_paper'),
        url(r'^mail_paper/(?P<pk>\d+)/$', views.mailPaperView, name='mail_paper'),
        url(r'^journal/(?P<journal>\d+)/$', views.searchView, name='journal'),
        url(r'^publisher/(?P<pk>\d+)/$', views.PublisherView.as_view(), name='publisher'),
        url(r'^sources$', views.sourcesView, name='sources'),
        url(r'^faq$', views.faqView, name='faq'),
        url(r'^feedback$', views.feedbackView, name='feedback'),
        url(r'^ajax/', include('papers.ajax')),
        url(r'^regular_login/$', views.regularLogin, name='regular_login'),
)
