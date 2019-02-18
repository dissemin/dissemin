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
from django.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render
from django.views import generic
from django.views.i18n import JavaScriptCatalog
import django_js_reverse.views

admin.autodiscover()

try:
    import importlib
except ImportError:
    from django.utils import importlib


def handler404(request, exception=None):
    response = render(request, '404.html', {'exception':exception})
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = render(request, '500.html', {'exception':exception})
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
        return render(request, name, {})
    return handler

js_info_dict = {
    'packages': (
        'dissemin'
    )
}

urlpatterns = [
    # Errors
    path(r'^404-error$', temp('404.html')),
    path(r'^500-error$', temp('500.html')),
    # Static views
    path(r'^sources$', temp('dissemin/sources.html'), name='sources'),
    path(r'^faq$', temp('dissemin/faq.html'), name='faq'),
    path(r'^tos$', temp('dissemin/tos.html'), name='tos'),
    path(r'^partners$', temp('dissemin/partners.html'), name='partners'),
    # Admin interface
    path(r'^admin/', admin.site.urls),
    # Apps
    path(r'^ajax-upload/', include('upload.urls')),
    path(r'^', include('papers.urls')),
    path(r'^', include('publishers.urls')),
    path(r'^', include('deposit.urls')),
    path(r'^', include('notification.urls')),
    path(r'^', include('autocomplete.urls')),
    path(r'^jsreverse/$', django_js_reverse.views.urls_js, name='js_reverse'),
    # Social auth
    path(r'^accounts/login/$', LoginView.as_view(), name='account_login'),
    path(r'^accounts/sandbox_login/$',
        SandboxLoginView.as_view(), name='sandbox-login'),
    path(r'^accounts/logout/$', logoutView, name='account_logout'),
    path(r'^accounts/social/', include('allauth.socialaccount.urls')),
    # JavaScript i18n
    path(r'^jsi18n/$', JavaScriptCatalog, js_info_dict, name='javascript-catalog'),
    path(r'^lang/', include('django.conf.urls.i18n'), name='set_language'),
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

# Debug toolbar
if 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns.append(
      path(r'^__debug__/', include(debug_toolbar.urls)))

