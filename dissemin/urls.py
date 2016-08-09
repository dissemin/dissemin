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


import allauth.account.views
from allauth.socialaccount import providers
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic
from django.views.i18n import javascript_catalog

from dissemin.settings import UNIVERSITY_BRANDING

admin.autodiscover()

try:
    import importlib
except ImportError:
    from django.utils import importlib


def handler404(request):
    response = render(request, '404.html')
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html')
    response.status_code = 500
    return response


class LoginView(generic.TemplateView):
    template_name = 'dissemin/login.html'


class SandboxLoginView(allauth.account.views.LoginView):
    template_name = 'dissemin/sandbox.html'


def logoutView(request):
    logout(request)
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('/')


def temp(name):
    def handler(request, *args, **kwargs):
        return render(request, name, UNIVERSITY_BRANDING)
    return handler

js_info_dict = {
    'packages': (
        'dissemin'
    )
}

urlpatterns = [
    # Errors
    url(r'^404-error$', temp('404.html')),
    url(r'^500-error$', temp('500.html')),
    # Static views
    url(r'^sources$', temp('dissemin/sources.html'), name='sources'),
    url(r'^faq$', temp('dissemin/faq.html'), name='faq'),
    url(r'^tos$', temp('dissemin/tos.html'), name='tos'),
    url(r'^feedback$', temp('dissemin/feedback.html'), name='feedback'),
    url(r'^partners$', temp('dissemin/partners.html'), name='partners'),
    # Authentication
    #url(r'^admin/logout/$','django_cas_ng.views.logout', name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    #url(r'^accounts/login/$', 'django_cas_ng.views.login', name='login'),
    #url(r'^accounts/logout/$','django_cas_ng.views.logout', name='logout'),
    #url(r'^logout/$', 'django_cas_ng.views.logout'),
    # Apps
    url(r'^ajax-upload/', include('upload.urls')),
    url(r'^', include('papers.urls')),
    url(r'^', include('publishers.urls')),
    url(r'^', include('deposit.urls')),
    url(r'^', include('notification.urls')),
    url(r'^jsreverse/$', 'django_js_reverse.views.urls_js', name='js_reverse'),
    # Social auth
    url(r'^accounts/login/$', LoginView.as_view(), name='account_login'),
    url(r'^accounts/sandbox_login/$',
        SandboxLoginView.as_view(), name='sandbox-login'),
    url(r'^accounts/logout/$', logoutView, name='account_logout'),
    url(r'^accounts/social/', include('allauth.socialaccount.urls')),
    # JavaScript i18n
    url(r'^jsi18n/$', javascript_catalog, js_info_dict, name='javascript-catalog'),
    url(r'^lang/', include('django.conf.urls.i18n'), name='set_language'),
    # Remove this in production
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT
           ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Allauth social providers (normally included directly in the standard installation
# of django-allauth, but as we disabled normal auth, we have to do it here).
for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.get_package() + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns
