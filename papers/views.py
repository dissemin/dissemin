# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views import generic
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from papers.tasks import *
from django.utils import timezone

from papers.models import *

# Number of papers shown on a search results page
NB_RESULTS_PER_PAGE = 20

def index(request):
    nb_researchers = Researcher.objects.count()
    nb_groups = ResearchGroup.objects.count()
    nb_departments = Department.objects.count()
    context = {
        'nb_researchers': nb_researchers,
        'nb_groups': nb_groups,
        'nb_departments': nb_departments,
        'departments': Department.objects.order_by('name')
        }
    return render(request, 'papers/index.html', context)

def searchView(request):
    context = dict()
    # Build the queryset
    queryset = Paper.objects.all()

    search_description = 'Papers'
    if 'researcher' in request.GET:
        researcher = get_object_or_404(Researcher, pk=request.GET.get('researcher'))
        queryset = queryset.filter(author__name__researcher=researcher)
        search_description += ' authored by '+unicode(researcher)
    elif 'department' in request.GET:
        department = get_object_or_404(Department, pk=request.GET.get('department'))
        queryset = queryset.filter(author__name__researcher__department=department)
        search_description += ' authored in '+unicode(department)
    if 'journal' in request.GET:
        journal = get_object_or_404(Journal, pk=request.GET.get('journal'))
        queryset = queryset.filter(publication__journal=journal)
        search_description += ' in '+unicode(journal)
    elif 'publisher' in request.GET:
        publisher = get_object_or_404(Publisher, pk=request.GET.get('publisher'))
        queryset = queryset.filter(publication__journal__publisher=publisher)
        seach_description += ' published by '+unicode(publisher)

    if search_description == 'Papers':
        search_description == 'All papers'

    # Sort
    queryset = queryset.order_by('-year')

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = request.GET.get('page')
    try:
        current_papers = paginator.page(page)
    except PageNotAnInteger:
        current_papers = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    context['search_results'] = current_papers
    context['search_description'] = search_description
    context['nb_results'] = queryset.count()

    return render(request, 'papers/search.html', context)

class ResearcherView(generic.DetailView):
    model = Researcher
    template_name = 'papers/researcher.html'

class GroupView(generic.DetailView):
    model = ResearchGroup
    template_name = 'papers/group.html'
    
class DepartmentView(generic.DetailView):
    model = Department
    template_name = 'papers/department.html'

class SourceView(generic.DetailView):
    model = OaiSource
    template_name = 'papers/oaiSource.html'

def updateResearcherOAI(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    fetch_records_for_researcher.apply_async(eta=timezone.now(), kwargs={'pk':pk})
    return render(request, 'papers/updateResearcher.html', {'researcher':source})

def updateResearcher(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    fetch_dois_for_researcher.apply_async(eta=timezone.now(), kwargs={'pk':pk})
    return render(request, 'papers/updateResearcher.html', {'researcher':source})

class PaperView(generic.DetailView):
    model = Paper
    template_name = 'papers/paper.html'

class JournalView(generic.DetailView):
    model = Journal
    template_name = 'papers/journal.html'

class PublisherView(generic.DetailView):
    model = Publisher
    template_name = 'papers/publisher.html'

