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
from papers.tasks import *

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
            if not created and Researcher.objects.filter(name=name).count() > 0:
                # we forbid the creation of two researchers with the same name,
                # although our model would support it (TODO ?)
                return HttpResponseForbidden('Researcher already present', content_type='text/plain')
            researcher = Researcher(
                    department=dept,
                    email=email,
                    role=role,
                    homepage=homepage,
                    name=name)
            researcher.save()
            name.update(is_known=True)
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

# Researcher management
@user_passes_test(is_admin)
def changeResearcher(request):
    allowedFields = ['role']
    return process_ajax_change(request, Researcher, allowedFields)

# Publisher management
@user_passes_test(is_admin)
def changePublisherStatus(request):
    allowedStatuses = [s[0] for s in OA_STATUS_CHOICES]
    try:
        pk = request.POST.get('pk')
        publisher = Publisher.objects.get(pk=pk)
        status = request.POST.get('status')
        if status in allowedStatuses and status != publisher.oa_status:
            change_publisher_oa_status.apply_async(eta=timezone.now(), kwargs={'pk':pk,'status':status})
            return HttpResponse('OK', content_type='text/plain')
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponseNotFound('NOK: '+message, content_type='text/plain')
    

urlpatterns = patterns('',
    url(r'^delete-paper-(?P<pk>\d+)$', deletePaper, name='ajax-deletePaper'),
    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-deleteResearcher'),
    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
    url(r'^change-researcher$', changeResearcher, name='ajax-changeResearcher'),
    url(r'^add-researcher$', addResearcher, name='ajax-addResearcher'),
    url(r'^change-publisher-status$', changePublisherStatus, name='ajax-changePublisherStatus'),
)

