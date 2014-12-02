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

def searchView(request, **kwargs):
    context = dict()
    # Build the queryset
    queryset = Paper.objects.all()
    args = request.GET.copy()
    args.update(kwargs)
    
    search_description = 'Papers'
    if 'researcher' in args:
        researcher = get_object_or_404(Researcher, pk=args.get('researcher'))
        queryset = queryset.filter(author__name__researcher=researcher)
        search_description += ' authored by '+unicode(researcher)
        context['researcher'] = researcher
    elif 'department' in args:
        department = get_object_or_404(Department, pk=args.get('department'))
        queryset = queryset.filter(author__name__researcher__department=department)
        search_description += ' authored in '+unicode(department)
        context['department'] = department
    if 'journal' in args:
        journal = get_object_or_404(Journal, pk=args.get('journal'))
        queryset = queryset.filter(publication__journal=journal)
        search_description += ' in '+unicode(journal)
        context['journal'] = journal
    elif 'publisher' in args:
        publisher = get_object_or_404(Publisher, pk=args.get('publisher'))
        queryset = queryset.filter(publication__journal__publisher=publisher)
        search_description += ' published by '+unicode(publisher)
        context['publisher'] = publisher
    if 'status' in args:
        queryset = queryset.filter(oa_status=args.get('status'))
        # We don't update the search description here, it will be displayed on the side
        context['status'] = args.get('status')
    if 'pdf' in args:
        val = args.get('pdf')
        if val == 'OK':
            queryset = queryset.filter(first_pdf_record__isnull=False)
        elif val == 'NOK':
            queryset = queryset.filter(first_pdf_record__isnull=True)
        context['pdf'] = val

    if search_description == 'Papers':
        search_description = 'All papers'

    # Sort
    queryset = queryset.order_by('-year')

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = args.get('page')
    try:
        current_papers = paginator.page(page)
    except PageNotAnInteger:
        current_papers = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)

    context['search_results'] = current_papers
    context['search_description'] = search_description
    context['nb_results'] = queryset.count()

    # Build the GET requests for variants of the parameters
    PDF_STATUS_CHOICES = [('OK', 'Available'),
                          ('NOK', 'Unavailable')]

    args_without_page = args.copy()
    if 'page' in args_without_page:
        del args_without_page['page']
    oa_variants = varyQueryArguments('status', args_without_page, OA_STATUS_CHOICES)
    pdf_variants = varyQueryArguments('pdf', args_without_page, PDF_STATUS_CHOICES)

    context['oa_status_choices'] = oa_variants
    context['pdf_status_choices'] = pdf_variants

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

