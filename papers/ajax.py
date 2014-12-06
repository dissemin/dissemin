# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound
from django.contrib.auth.decorators import user_passes_test

from papers.models import *
from papers.user import is_admin

@user_passes_test(is_admin)
def deletePaper(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    paper.visibility = 'DELETED'
    paper.save(update_fields=['visibility'])
    return HttpResponse('OK', content_type='text/plain')

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

@user_passes_test(is_admin)
def changeDepartment(request):
    allowedFields = ['name']
    return process_ajax_change(request, Department, allowedFields)

@user_passes_test(is_admin)
def changePaper(request):
    allowedFields = ['title']
    return process_ajax_change(request, Paper, allowedFields)


urlpatterns = patterns('',
    url(r'^delete-paper-(?P<pk>\d+)$', deletePaper, name='ajax-deletePaper'),
    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
)

