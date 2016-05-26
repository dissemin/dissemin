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

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.template import RequestContext, loader
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.db.models import Count

from datetime import datetime

from celery.execute import send_task

from papers.models import *
from papers.forms import *
from papers.user import is_admin, is_authenticated
from papers.orcid import *
from papers.doi import to_doi

from notification.api import get_notifications

from deposit.models import *

from publishers.views import varyQueryArguments
from publishers.models import OA_STATUS_CHOICES
from statistics.models import COMBINED_STATUS_CHOICES, STATUS_QUERYSET_FILTER, PDF_STATUS_CHOICES, BareAccessStatistics
from dissemin.settings import MEDIA_ROOT, UNIVERSITY_BRANDING, DEPOSIT_MAX_FILE_SIZE 

from allauth.socialaccount.signals import post_social_login

import json

class SlugDetailView(generic.DetailView):
    """
    A DetailView for objects with a slug field for human-friendly URLs:
    redirects if the slug in the request does not match the object's slug.
    """
    view_name = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if kwargs.get('slug') == self.object.slug:
            context = self.get_context_data(object=self.object, **kwargs)
            return self.render_to_response(context)
        else:
            kwargs['slug'] = self.object.slug
            return redirect(self.view_name, permanent=True, **kwargs)

def fetch_on_orcid_login(sender, **kwargs):
    account = kwargs['sociallogin'].account

    # Only prefetch if the social login refers to a valid ORCID account
    orcid = validate_orcid(account.uid)
    if not orcid:
        return

    profile = account.extra_data
    user = None
    if '_user_cache' in account.__dict__:
        user = account.user
    r = Researcher.get_or_create_by_orcid(orcid, profile, user)
    if r.user_id is None and user is not None:
        r.user = user
        r.save(update_fields=['user'])
    if r.empty_orcid_profile is None:
        r.init_from_orcid()
    else:
        r.fetch_everything_if_outdated()

post_social_login.connect(fetch_on_orcid_login)

# Number of papers shown on a search results page
NB_RESULTS_PER_PAGE = 20

def index(request):
    """
    View for the home page
    """
    context = {
        'papers' : Paper.objects.filter(visibility='VISIBLE').order_by('-pubdate')[:5],
        'newResearcherForm' : AddUnaffiliatedResearcherForm(),
        }
    context.update(UNIVERSITY_BRANDING)
    return render(request, 'papers/index.html', context)

def searchView(request, **kwargs):
    """
    Any view that returns a list of papers can be expressed using this "search" view.
    It allows to select a list of papers based on a list of criteria (but no keyword search for now).
    """
    context = dict()
    # Build the queryset
    queryset = Paper.objects.all()
    args = request.GET.copy()
    args.update(kwargs)

    if 'journal' in args and not is_admin(request.user):
        del args['journal']
    
    search_description = _('Papers')
    head_search_description = _('Papers')

    context['researcher_id'] = None
    if 'researcher' in args or 'orcid' in args:
        researcher = None
        if 'researcher' in args:
            researcher = get_object_or_404(Researcher, pk=args.get('researcher'))
        elif 'orcid' in args:
            try:
                researcher = Researcher.objects.get(orcid=args.get('orcid'))
            except Researcher.DoesNotExist:
                orcid = validate_orcid(args.get('orcid'))
                researcher = Researcher.get_or_create_by_orcid(orcid)
                researcher.init_from_orcid()

        # Slug parameter is None if 'orcid' in args
        if args.get('slug') != researcher.slug:
            kwargs['slug'] = researcher.slug
            return redirect('researcher', permanent=True, **kwargs)

        queryset = queryset.filter(author__researcher=researcher)
        search_description += _(' authored by ')+unicode(researcher)
        head_search_description = unicode(researcher)
        context['researcher'] = researcher
        context['researcher_id'] = researcher.id
        context['breadcrumbs'] = researcher.breadcrumbs()
    elif 'department' in args:
        dept = get_object_or_404(Department, pk=args.get('department'))
        queryset = queryset.filter(author__researcher__department=dept)
        search_description = unicode(dept)
        head_search_description = unicode(dept)
        context['department'] = dept
        context['breadcrumbs'] = dept.breadcrumbs()+[(_('Papers'), '')]
    elif 'name' in args:
        name = get_object_or_404(Name, pk=args.get('name'))
        queryset = queryset.filter(author__name=name)
        search_description += _(' authored by ')+unicode(name)
        head_search_description = unicode(name)
        context['name'] = name
    if 'journal' in args:
        journal = get_object_or_404(Journal, pk=args.get('journal'))
        queryset = queryset.filter(oairecord__journal=journal)
        search_description += _(' in ')+unicode(journal)
        context['journal'] = journal
        context['breadcrumbs'] = journal.breadcrumbs()
    elif 'publisher' in args:
        publisher = get_object_or_404(Publisher, pk=args.get('publisher'))
        queryset = queryset.filter(oairecord__publisher=publisher)
        search_description += _(' published by ')+unicode(publisher)
        head_search_description = unicode(publisher)
        context['publisher'] = publisher
        context['breadcrumbs'] = publisher.breadcrumbs()+[(_('Papers'),'')]
    if 'state' in args:
        state = args.get('state')
        context['state'] = state
        state_filter = STATUS_QUERYSET_FILTER.get(state)
        if state_filter is not None:
            queryset = state_filter(queryset)
    if 'status' in args:
        queryset = queryset.filter(oa_status=args.get('status'))
        # We don't update the search description here, it will be displayed on the side
        context['status'] = args.get('status')
    if 'pdf' in args:
        val = args.get('pdf')
        if val == 'OK':
            queryset = queryset.filter(pdf_url__isnull=False)
        elif val == 'NOK':
            queryset = queryset.filter(pdf_url__isnull=True)
        context['pdf'] = val
    if 'pubtype' in args:
        val = args.get('pubtype')
        if val in PAPER_TYPE_PREFERENCE:
            queryset = queryset.filter(doctype=val)
        context['pubtype'] = val
    if 'visibility' in args and is_admin(request.user):
        val = args.get('visibility')
        if val in [x[0] for x in VISIBILITY_CHOICES]:
            queryset = queryset.filter(visibility=val)
        context['visibility'] = val
    else:
        queryset = queryset.filter(visibility='VISIBLE')
        context['visibility'] = 'VISIBLE'

    if search_description == _('Papers'):
        context['breadcrumbs'] = [(search_description,'')]
        search_description = _('All papers')

    # Sort
    queryset = queryset.order_by('-pubdate')
    # Make distinct
    queryset = queryset.distinct()
    # Create stats
    stats = BareAccessStatistics.from_queryset(queryset)

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = args.get('page')
    try:
        current_papers = paginator.page(page)
    except PageNotAnInteger:
        current_papers = paginator.page(1)
    except EmptyPage:
        current_papers = paginator.page(paginator.num_pages)

    context['search_stats'] = stats
    context['search_results'] = current_papers
    context['search_description'] = search_description
    context['head_search_description'] = head_search_description
    context['nb_results'] = paginator.count
    context['ajax_url'] = reverse('ajax-search')+'?'+urlencode(args) 

    # Notifications
    # TODO: unefficient query.
    notifications = get_notifications(request)
    selected_messages = map(lambda n: n.serialize_to_json(),
            sorted(notifications, key=lambda msg: msg.level)[:3])
    context['messages'] = selected_messages

    # Build the GET requests for variants of the parameters
    args_without_page = args.copy()
    if 'page' in args_without_page:
        del args_without_page['page']
    oa_variants = varyQueryArguments('status', args_without_page, OA_STATUS_CHOICES)
    pdf_variants = varyQueryArguments('pdf', args_without_page, PDF_STATUS_CHOICES)
    pubtype_variants = varyQueryArguments('pubtype', args_without_page, PAPER_TYPE_CHOICES)
    visibility_variants = varyQueryArguments('visibility', args_without_page, VISIBILITY_CHOICES)
    state_variants = varyQueryArguments('state', args_without_page, COMBINED_STATUS_CHOICES)

    context['oa_status_choices'] = oa_variants
    context['pdf_status_choices'] = pdf_variants
    context['state_choices'] = state_variants
    context['pubtype_status_choices'] = pubtype_variants
    context['visibility_choices'] = visibility_variants

    if request.META.get('CONTENT_TYPE') == 'application/json' and 'researcher' in context:
        researcher = context['researcher']
        context['request'] = request
        response = {}
        response['listPapers'] = loader.render_to_string('papers/ajaxListPapers.html', context)
        response['stats'] = json.loads(stats.pie_data(researcher.object_id))
        response['stats']['numtot'] = stats.num_tot
        response['messages'] = selected_messages
        if researcher.current_task:
            response['status'] = researcher.current_task
            response['display'] = researcher.get_current_task_display()
        return HttpResponse(json.dumps(response), content_type="application/json")
    return render(request, 'papers/search.html', context)

@user_passes_test(is_admin)
def reclusterResearcher(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    send_task('recluster_researcher', [], {'pk':pk})
    return redirect(request.META['HTTP_REFERER'])

@user_passes_test(is_authenticated)
def refetchResearcher(request, pk):
    researcher = get_object_or_404(Researcher, pk=pk)
    if researcher.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Not authorized to update papers for this researcher.")
    send_task('fetch_everything_for_researcher', [], {'pk':pk})
    return redirect(request.META['HTTP_REFERER'])

class ResearcherView(generic.DetailView):
    model = Researcher
    template_name = 'papers/researcher.html'

@user_passes_test(is_authenticated)
def myProfileView(request):
    try:
        r = Researcher.objects.get(user=request.user)
        return searchView(request, researcher=r.pk)
    except Researcher.DoesNotExist:
        return render(request, 'papers/createProfile.html')

class DepartmentView(generic.DetailView):
    model = Department
    template_name = 'papers/department.html'
    def get_context_data(self, **kwargs):
        context = super(DepartmentView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.object.breadcrumbs()
        return context

class InstitutionView(generic.DetailView):
    model = Institution
    template_name = 'papers/institution.html'
    def get_context_data(self, **kwargs):
        context = super(InstitutionView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.object.breadcrumbs()
        return context

class PaperView(SlugDetailView):
    model = Paper
    template_name = 'papers/paper.html'
    view_name = 'paper'

    def departments(self):
        paper = self.object
        return Department.objects.filter(researcher__author__paper=paper).distinct()

    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk', None)
        doi = self.kwargs.get('doi', None)
        if doi:
            doi = to_doi(doi)

        try:
            if pk is not None:
                paper = queryset.get(pk=pk)
            elif doi is not None:
                paper = Paper.objects.get(oairecord__doi=doi)
            else:
                raise AttributeError("Paper view expects a DOI or a pk")
        except ObjectDoesNotExist:
            paper = Paper.create_by_doi(doi)
            if paper is None:
                raise Http404(_("No %(verbose_name)s found matching the query") %
                        {'verbose_name': Paper._meta.verbose_name})
        return paper

    def get_context_data(self, **kwargs):
        context = super(PaperView, self).get_context_data(**kwargs)
        context['breadcrumbs'] = self.object.breadcrumbs()
        if 'deposit' in self.request.GET:
            try:
                pk = int(self.request.GET['deposit'])
                dep = DepositRecord.objects.get(pk=pk)
                if dep.paper_id == self.object.id:
                    context['deposit'] = dep
            except (TypeError, ValueError, DepositRecord.DoesNotExist):
                pass
        return context


@user_passes_test(is_admin)
def mailPaperView(request, pk):
    source = get_object_or_404(Paper, pk=pk)
    if source.can_be_asked_for_upload():
        send_email_for_paper(source) 
        return render(request, 'papers/mail_paper.html', {'paper':source})
    else:
        return HttpResponseForbidden()

def annotationsView(request):
    return render(request, 'papers/annotations.html', {'annotations':Annotation.objects.all(),
        'users':User.objects.all()})

class AnnotationsView(generic.TemplateView):
    template_name = 'papers/annotations.html'
    def users(self):
        users = list(User.objects.all().annotate(num_annot=Count('annotation')))
        sorted_users = sorted(users, key=lambda x:-x.num_annot)
        filtered_users = filter(lambda x:x.num_annot > 0, sorted_users)
        return sorted_users

