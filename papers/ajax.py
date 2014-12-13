# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import validate_email
from django.forms import ValidationError
from django.db import IntegrityError
import json

from django.views.decorators.csrf import csrf_exempt

from papers.models import *
from papers.user import is_admin
from papers.forms import AddResearcherForm
from papers.utils import iunaccent

# General function used to change a CharField in a model with ajax
def process_ajax_change(request, model, allowedFields):
    try:
        dept = model.objects.get(pk=request.POST.get('pk'))
        field = request.POST.get('name')
        if field in allowedFields:
            setattr(dept, field, request.POST.get('value'))
            dept.save(update_fields=[field])
            return HttpResponse('OK', content_type='text/plain')
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponseNotFound('NOK', content_type='text/plain')

# Researcher management
@user_passes_test(is_admin)
def deleteResearcher(request, pk):
    researcher = get_object_or_404(Researcher, pk=pk)
    researcher.delete()
    return HttpResponse('OK', content_type='text/plain')

@user_passes_test(is_admin)
def addResearcher(request):
    form = AddResearcherForm(request.POST)
    if form.is_valid():
        try:
            dept = form.cleaned_data['department']
            email = form.cleaned_data['email']
            first = form.cleaned_data['first']
            last = form.cleaned_data['last']
            role = form.cleaned_data['role']
            homepage = form.cleaned_data['homepage']

            name, created = Name.objects.get_or_create(full=iunaccent(first+' '+last),
                    defaults={'first':first, 'last':last})
            if not created and name.researcher != None:
                    return HttpResponseForbidden('Researcher already present', content_type='text/plain')
            researcher = Researcher(
                    department=dept,
                    email=email,
                    role=role,
                    homepage=homepage)
            researcher.save()
            name.researcher = researcher
            name.save(update_fields=['researcher'])
            return HttpResponse(json.dumps({
                'id':researcher.id,
                'name':first+' '+last}), content_type='application/javascript')
        except IntegrityError as e:
            print "integrity error"
            print e
            return HttpResponseForbidden('Invalid input, something went wrong', content_type='text/plain')
    else:
        print json.dumps(form.errors)
        return HttpResponseForbidden(json.dumps(form.errors), content_type='application/javascript')

# Paper management
@user_passes_test(is_admin)
def deletePaper(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    paper.visibility = 'DELETED'
    paper.save(update_fields=['visibility'])
    return HttpResponse('OK', content_type='text/plain')

@user_passes_test(is_admin)
def changePaper(request):
    allowedFields = ['title']
    return process_ajax_change(request, Paper, allowedFields)

# Department management
@user_passes_test(is_admin)
def changeDepartment(request):
    allowedFields = ['name']
    return process_ajax_change(request, Department, allowedFields)



urlpatterns = patterns('',
    url(r'^delete-paper-(?P<pk>\d+)$', deletePaper, name='ajax-deletePaper'),
    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-deleteResearcher'),
    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
    url(r'^add-researcher$', addResearcher, name='ajax-addResearcher'),
)

