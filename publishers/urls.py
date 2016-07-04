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

from publishers import views

urlpatterns = [
        url(r'^publishers$', views.PublishersView.as_view(), name='publishers'),
        url(r'^publisher/(?P<pk>\d+)/$', views.PublisherView.as_view()), # Deprecated URL
        url(r'^b/(?P<pk>\d+)/(?P<slug>[\w-]*)$', views.PublisherView.as_view(), name='publisher'),
]

