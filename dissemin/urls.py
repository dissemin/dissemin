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
from os.path import join

from django.contrib import admin
from dissemin.settings import UNIVERSITY_BRANDING
admin.autodiscover()

def handler404(request):
    response = render(request, '404.html')
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html')
    response.status_code = 500
    return response

def temp(name):
    return (lambda x: render(x, name, UNIVERSITY_BRANDING))

urlpatterns = patterns('',
    # Errors
    url(r'^404-error$', temp('404.html')),
    url(r'^500-error$', temp('500.html')),
    # Static views
    url(r'^sources$', temp('dissemin/sources.html'), name='sources'),
    url(r'^faq$', temp('dissemin/faq.html'), name='faq'),
    url(r'^tos$', temp('dissemin/tos.html'), name='tos'),
    url(r'^feedback$', temp('dissemin/feedback.html'), name='feedback'),
    # Authentication
    url(r'^admin/logout/$','django_cas_ng.views.logout', name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django_cas_ng.views.login', name='login'), 
    url(r'^accounts/logout/$','django_cas_ng.views.logout', name='logout'),
    url(r'^logout/$', 'django_cas_ng.views.logout'),
    # Apps
    url(r'^ajax-upload/', include('upload.urls')),
    url(r'^', include('papers.urls')),
    url(r'^', include('publishers.urls')),
    url(r'^', include('deposit.urls')),
# Remove this in production
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
