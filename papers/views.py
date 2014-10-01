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

def updateSource(request, pk):
    source = get_object_or_404(OaiSource, pk=pk)
    fetch_items_from_oai_source.apply_async(eta=timezone.now(), kwargs={'pk':pk})
    return render(request, 'papers/updateSource.html', {'source':source})

def updateResearcher(request, pk):
    source = get_object_or_404(Researcher, pk=pk)
    fetch_dois_for_researcher.apply_async(eta=timezone.now(), kwargs={'pk':pk})
    return render(request, 'papers/updateResearcher.html', {'researcher':source})

def checkPublicationAvailability(request, pk):
    publi = get_object_or_404(Publication, pk=pk)
    check_full_text_for_publication.apply_async(eta=timezone.now(), kwargs={'pk':pk})
    return render(request, 'papers/updatePublication.html', {'publication':publi})

class PaperView(generic.DetailView):
    model = Paper
    template_name = 'papers/paper.html'

