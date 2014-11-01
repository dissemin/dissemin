from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views import generic
from papers.tasks import *
from django.utils import timezone

from papers.models import *

def index(request):
    nb_researchers = Researcher.objects.count()
    nb_groups = ResearchGroup.objects.count()
    nb_departments = Department.objects.count()
    context = {
        'nb_researchers': nb_researchers,
        'nb_groups': nb_groups,
        'nb_departments': nb_departments
        }
    return render(request, 'papers/index.html', context)

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
    return render(request, 'papers/updateResearcher.html', {'source':source})

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

