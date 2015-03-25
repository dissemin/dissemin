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

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import logout
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from django.utils.translation import ugettext as _

from celery.execute import send_task

from papers.models import *
from papers.forms import *
from papers.user import is_admin, is_authenticated

# Number of papers shown on a search results page
NB_RESULTS_PER_PAGE = 20
# Number of journals per page on a Publisher page
NB_JOURNALS_PER_PAGE = 30

def index(request):
    
    context = {
        'nb_researchers': Researcher.objects.count(),
        'nb_departments': Department.objects.count(),
        'nb_papers': Paper.objects.filter(visibility='VISIBLE').count(),
        'nb_publishers': Publisher.objects.filter(stats__num_tot__gt=0).count(),
        'departments': Department.objects.order_by('name').select_related('stats')[:3],
        'papers' : Paper.objects.filter(visibility='VISIBLE').order_by('-pubdate')[:5],
        'publishers' : Publisher.objects.all().filter(stats__isnull=False).order_by('-stats__num_tot')[:3],
        }
    return render(request, 'papers/index.html', context)

def publishersView(request, **kwargs):
    context = dict()
    # Build the queryset
    queryset = Publisher.objects.all()
    args = request.GET.copy()
    args.update(kwargs)

    search_description = _('Publishers')
    if 'status' in args:
        queryset = queryset.filter(oa_status=args.get('status'))
        context['status'] = args.get('status')

    # Ordering
    # queryset = queryset.order_by('name')
    queryset = queryset.order_by('-stats__num_tot')
    queryset = queryset.select_related('stats')

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = args.get('page')
    try:
        current_publishers = paginator.page(page)
    except PageNotAnInteger:
        current_publishers = paginator.page(1)
    except EmptyPage:
        current_publishers = paginator.page(paginator.num_pages)

    context['search_results'] = current_publishers
    context['search_description'] = search_description
    context['nb_results'] = queryset.count()

    # Build the GET requests for variants of the parameters
    args_without_page = args.copy()
    if 'page' in args_without_page:
        del args_without_page['page']
    oa_variants = varyQueryArguments('status', args_without_page, OA_STATUS_CHOICES)

    context['oa_status_choices'] = oa_variants
    return render(request, 'papers/publishers.html', context)

def departmentsView(request, **kwargs):
	context = {
        'nb_departments': Department.objects.count(),
        'departments': Department.objects.order_by('name').select_related('stats'),
        }
	return render(request, 'papers/departments.html', context)

def searchView(request, **kwargs):
    context = dict()
    # Build the queryset
    queryset = Paper.objects.all()
    args = request.GET.copy()
    args.update(kwargs)
    
    search_description = _('Papers')
    head_search_description = _('Papers')

    context['researcher_id'] = None
    if 'researcher' in args:
        researcher = get_object_or_404(Researcher, pk=args.get('researcher'))
        queryset = queryset.filter(author__researcher=researcher)
        search_description += _(' authored by ')+unicode(researcher)
        head_search_description = unicode(researcher)
        context['researcher'] = researcher
        context['researcher_id'] = researcher.id
    elif 'department' in args:
        department = get_object_or_404(Department, pk=args.get('department'))
        queryset = queryset.filter(author__researcher__department=department)
        search_description += _(' authored in ')+unicode(department)
        head_search_description = unicode(department)
        context['department'] = department
    elif 'name' in args:
        name = get_object_or_404(Name, pk=args.get('name'))
        queryset = queryset.filter(author__name=name)
        search_description += _(' authored by ')+unicode(name)
        head_search_description = unicode(name)
        context['name'] = name
    if 'journal' in args:
        journal = get_object_or_404(Journal, pk=args.get('journal'))
        queryset = queryset.filter(publication__journal=journal)
        search_description += _(' in ')+unicode(journal)
        context['journal'] = journal
    elif 'publisher' in args:
        publisher = get_object_or_404(Publisher, pk=args.get('publisher'))
        queryset = queryset.filter(publication__publisher=publisher)
        search_description += _(' published by ')+unicode(publisher)
        head_search_description = unicode(publisher)
        context['publisher'] = publisher
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
        search_description = _('All papers')

    # Sort
    queryset = queryset.order_by('-pubdate')
    # Make distinct
    queryset = queryset.distinct()

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = args.get('page')
    try:
        current_papers = paginator.page(page)
    except PageNotAnInteger:
        current_papers = paginator.page(1)
    except EmptyPage:
        current_papers = paginator.page(paginator.num_pages)

    context['search_results'] = current_papers
    context['search_description'] = search_description
    context['head_search_description'] = head_search_description
    context['nb_results'] = paginator.count

    # Build the GET requests for variants of the parameters
    args_without_page = args.copy()
    if 'page' in args_without_page:
        del args_without_page['page']
    oa_variants = varyQueryArguments('status', args_without_page, OA_STATUS_CHOICES)
    pdf_variants = varyQueryArguments('pdf', args_without_page, PDF_STATUS_CHOICES)
    pubtype_variants = varyQueryArguments('pubtype', args_without_page, PAPER_TYPE_CHOICES)
    visibility_variants = varyQueryArguments('visibility', args_without_page, VISIBILITY_CHOICES)

    context['oa_status_choices'] = oa_variants
    context['pdf_status_choices'] = pdf_variants
    context['pubtype_status_choices'] = pubtype_variants
    context['visibility_choices'] = visibility_variants

    return render(request, 'papers/search.html', context)

def varyQueryArguments(key, args, possibleValues):
    variants = []
    for s in possibleValues:
        queryargs = args.copy()
        if s[0] != queryargs.get(key):
            queryargs[key] = s[0]
        else:
            queryargs.pop(key)
        variants.append((s[0], s[1], queryargs))
    return variants

def logoutView(request):
    logout(request)
    if 'HTTP_REFERER' in request.META:
        return redirect(request.META['HTTP_REFERER'])
    else:
        return redirect('/')

@user_passes_test(is_admin)
def updateResearcherOAI(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    send_task('fetch_records_for_researcher', [], {'pk':pk})
    return render(request, 'papers/updateResearcher.html', {'researcher':source})

@user_passes_test(is_admin)
def updateResearcher(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    send_task('fetch_dois_for_researcher', [], {'pk':pk})
    return render(request, 'papers/updateResearcher.html', {'researcher':source})

class ResearcherView(generic.DetailView):
    model = Researcher
    template_name = 'papers/researcher.html'

class GroupView(generic.DetailView):
    model = ResearchGroup
    template_name = 'papers/group.html'
    
class DepartmentView(generic.DetailView):
    model = Department
    template_name = 'papers/department.html'
    def get_context_data(self, **kwargs):
        context = super(DepartmentView, self).get_context_data(**kwargs)
        context['add_form'] = AddResearcherForm()
        return context

class PaperView(generic.DetailView):
    model = Paper
    template_name = 'papers/paper.html'

class JournalView(generic.DetailView):
    model = Journal
    template_name = 'papers/journal.html'

class PublisherView(generic.DetailView):
    model = Publisher
    template_name = 'papers/publisher.html'
    def get_context_data(self, **kwargs):
        context = super(PublisherView, self).get_context_data(**kwargs)
        context['oa_status_choices'] = OA_STATUS_CHOICES
        # Build the paginator
        publisher = context['publisher']
        paginator = Paginator(publisher.sorted_journals, NB_JOURNALS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            current_journals = paginator.page(page)
        except PageNotAnInteger:
            current_journals = paginator.page(1)
        except EmptyPage:
            current_journals = paginator.page(paginator.num_pages)
        context['journals'] = current_journals
        return context

def sourcesView(request):
    return render(request, 'papers/sources.html')

def faqView(request):
    return render(request, 'papers/faq.html')

def feedbackView(request):
    return render(request, 'papers/feedback.html')

def regularLogin(request):
    return auth_login(request, 'papers/login.html')

