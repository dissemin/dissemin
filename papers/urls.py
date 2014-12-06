# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

from papers import views, ajax

urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^login/$', login, {'template_name': 'admin/login.html'}),
        url(r'^logout/$', views.logoutView, name='logout'),
        url(r'^search', views.searchView, name='search'),
        url(r'^researcher/(?P<researcher>\d+)/$', views.searchView, name='researcher'),
        url(r'^researcher/(?P<pk>\d+)/update/$', views.updateResearcher, name='updateResearcher'),
        url(r'^researcher/(?P<pk>\d+)/updateoai/$', views.updateResearcherOAI, name='updateResearcherOAI'),
        url(r'^group/(?P<pk>\d+)/$', views.GroupView.as_view(), name='group'),
        url(r'^department/(?P<pk>\d+)/$', views.DepartmentView.as_view(), name='department'),
        url(r'^source/(?P<pk>\d+)/$', views.SourceView.as_view(), name='source'),
        url(r'^paper/(?P<pk>\d+)/$', views.PaperView.as_view(), name='paper'),
        url(r'^journal/(?P<journal>\d+)/$', views.searchView, name='journal'),
        url(r'^publisher/(?P<pk>\d+)/$', views.PublisherView.as_view(), name='publisher'),
        url(r'^ajax/', include('papers.ajax')),
)
