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

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

from django.contrib import admin
admin.autodiscover()

def handler404(request):
    response = render(request, '404.html')
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html')
    response.status_code = 500
    return response

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'dissemin.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^404-error$', (lambda x: render(x, '404.html'))),
    url(r'^500-error$', (lambda x: render(x, '500.html'))),
    url(r'^admin/logout/$','django_cas_ng.views.logout', name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django_cas_ng.views.login', name='login'), 
    url(r'^accounts/logout/$','django_cas_ng.views.logout', name='logout'),
    url(r'^logout/$', 'django_cas_ng.views.logout'),
    url(r'^ajax-upload/', include('upload.urls')),
    url(r'^', include('papers.urls')),
    url(r'^', include('publishers.urls')),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
