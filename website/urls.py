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


import django_js_reverse.views

from allauth.socialaccount import providers

from django.conf import settings
from django.urls import include
from django.urls import path
from django.urls import re_path
from django.urls import register_converter
from django.urls.converters import StringConverter
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.i18n import JavaScriptCatalog

from autocomplete.views import affiliation_autocomplete
from deposit.views import get_metadata_form
from deposit.views import GlobalPreferencesView
from deposit.views import LetterDeclarationView
from deposit.views import MyDepositsView
from deposit.views import RepositoryPreferencesView
from deposit.views import start_view
from deposit.views import submitDeposit
from papers.ajax import claimPaper
from papers.ajax import unclaimPaper
from papers.ajax import deleteResearcher
from papers.ajax import todo_list_add
from papers.ajax import todo_list_remove
from papers.ajax import waitForConsolidatedField
from papers.api import api_paper_doi
from papers.api import api_paper_pk
from papers.api import api_paper_query
from papers.api import PaperSearchAPI
from papers.api import ResearcherAPI
from papers.views import AdvancedPaperSearchView
from papers.views import MyProfileView
from papers.views import MyTodoListView
from papers.views import PaperSearchView
from papers.views import PaperView
from papers.views import ResearcherView
from papers.views import redirect_by_doi
from papers.views import refetch_researcher
from publishers.ajax import change_publisher_status
from publishers.views import PublisherView
from publishers.views import PublishersView
from upload.views import handleAjaxUpload
from upload.views import handleUrlDownload
from website.views import LoginView

from website.views import StartPageView

try:
    import importlib
except ImportError:
    from django.utils import importlib

# We define our own slug converter, since we want to allow empty slugs
class SlugConverter(StringConverter):
    regex = '[-a-zA-Z0-9_]*'

register_converter(SlugConverter, 'slug')


def handler403(request, exception=None):
    response = render(request, '403.html', {'exception':exception})
    response.status_code = 403
    return response


def handler404(request, exception=None):
    response = render(request, '404.html', {'exception':exception})
    response.status_code = 404
    return response


def handler500(request, exception=None):
    response = render(request, '500.html', {'exception':exception})
    response.status_code = 500
    return response


def logoutView(request):
    logout(request)
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('/')

js_info_dict = {
    'packages': (
        'dissemin'
    )
}

urlpatterns = [
    # Start page
    path('', StartPageView.as_view(), name='start-page'),
    # Paper related pages
    path('advanced-search/', AdvancedPaperSearchView.as_view(), name='advanced-search'),
    path('p/<int:pk>/<slug:slug>/', PaperView.as_view(), name='paper'),
    path('p/<int:pk>/', PaperView.as_view(), name='paper'),
    re_path(r'^(?P<doi>10\..*)', PaperView.as_view(), name='paper-doi'),
    re_path(r'p/direct/(?P<doi>10\..*)', redirect_by_doi, name='paper-redirect-doi'),
    path('search/', PaperSearchView.as_view(), name='search'),
    # Publisher related pages
    path('publishers/', PublishersView.as_view(), name='publishers'),
    path('b/<int:pk>/<slug:slug>/', PublisherView.as_view(), name='publisher'),
    path('b/<int:pk>/', PublisherView.as_view(), name='publisher'),
    # Researcher realted pages
    path('r/<int:researcher>/<slug:slug>/', ResearcherView.as_view(), name='researcher'),
    path('r/<int:researcher>/', ResearcherView.as_view(), name='researcher'),
    re_path(r'^(?P<orcid>[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9])/$', ResearcherView.as_view(), name='researcher-by-orcid'),
    # Upload related pages
    path('autocomplete/hal/affiliation/', affiliation_autocomplete, name='autocomplete-hal-affiliations'),
    path('deposit/letter-of-declaration/<int:pk>/', LetterDeclarationView.as_view(), name='letter-of-declaration'),
    path('deposit/paper/<int:pk>/', start_view, name='upload-paper'),
    # User related pages
    path('my-profile/', MyProfileView.as_view(), name='my-profile'),
    path('my-todolist/', MyTodoListView.as_view(), name='my-todolist'),
    # Static pages
    path('faq/', TemplateView.as_view(template_name='dissemin/faq.html'), name='faq'),
    path('sources/', TemplateView.as_view(template_name='dissemin/sources.html'), name='sources'),
    path('tos/', TemplateView.as_view(template_name='dissemin/tos.html'), name='tos'),
    # API
    path('api/p/<int:pk>', api_paper_pk, name='api-paper-pk'),
    path('api/r/<int:researcher>/<slug:slug>/', ResearcherAPI.as_view(), name='api-researcher-id'),
    path('api/r/<int:researcher>/', ResearcherAPI.as_view(), name='api-researcher-id'),
    path('api/query/', api_paper_query, name='api-paper-query'),
    path('api/search/', PaperSearchAPI.as_view(), name='api-paper-search'),
    re_path(r'^api/(?P<doi>10\..*)$', api_paper_doi, name='api-paper-doi'),
    # AJAX
    path('ajax/change_publisher_status/', change_publisher_status, name='ajax_change_publisher_status'),
    path('ajax/delete-researcher/<int:pk>/', deleteResearcher, name='ajax-delete-researcher'),
    path('ajax/download-url/', handleUrlDownload, name='ajax-downloadUrl'),
    path('ajax/get-metadata.form/', get_metadata_form, name='ajax-get-metadata-form'),
    path('ajax/paper-claim/', claimPaper, name='ajax-claimPaper'),
    path('ajax/paper-unclaim/', unclaimPaper, name='ajax-unclaimPaper'),
    path('ajax/researcher/<int:pk>/update/', refetch_researcher, name='refetch-researcher'),
    path('ajax/submit-deposit/<int:pk>/', submitDeposit, name='ajax-submit-deposit'),
    path('ajax/todolist-add/', todo_list_add, name='ajax-todolist-add'),
    path('ajax/todolist-remove/', todo_list_remove, name='ajax-todolist-remove'),
    path('ajax/upload-fulltext/', handleAjaxUpload, name='ajax-uploadFulltext'),
    path('ajax/wait-for-consolidated-field/', waitForConsolidatedField, name='ajax-waitForConsolidatedField'),
    # Use related pages
    path('my-deposits', MyDepositsView.as_view(), name='my-deposits'),
    path('preferences/global/', GlobalPreferencesView.as_view(), name='preferences-global'),
    path('preferences/repository/<int:pk>/', RepositoryPreferencesView.as_view(), name='preferences-repository'),
    # Admin interface
    path('admin/', admin.site.urls),
    # We keep notification urls, because the app is rather opaque
    path('', include('notification.urls')),
    path('jsreverse/', django_js_reverse.views.urls_js, name='js_reverse'),
    # Shibboleth Discovery
    path('shib-ds/', include('shibboleth_discovery.urls')),
    # Social auth
    path('accounts/login/', LoginView.as_view(), name='account-login'),
    path('accounts/logout/', logoutView, name='account-logout'),
    path('accounts/social/', include('allauth.socialaccount.urls')),
    # JavaScript i18n
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('lang/', include('django.conf.urls.i18n'), name='set_language'),
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
      path('__debug__/', include(debug_toolbar.urls)))

