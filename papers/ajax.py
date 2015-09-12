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

from django.conf.urls import patterns, include, url
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.core.validators import validate_email
from django.core.exceptions import MultipleObjectsReturned
from django.template import loader
from django.forms import ValidationError
from django.db import IntegrityError
from django.utils.translation import ugettext as __
import json, requests

from django.views.decorators.csrf import csrf_exempt
from celery.execute import send_task

from dissemin.settings import URL_DEPOSIT_DOWNLOAD_TIMEOUT, DEPOSIT_MAX_FILE_SIZE, DEPOSIT_CONTENT_TYPES, MEDIA_ROOT

from papers.models import *
from papers.user import *
from papers.forms import AddResearcherForm, AddUnaffiliatedResearcherForm
from papers.utils import iunaccent, sanitize_html, kill_html

import os.path

# General function used to change a CharField in a model with ajax
def process_ajax_change(request, model, allowedFields):
    response = dict()
    try:
        instance = model.objects.get(pk=request.POST.get('pk'))
        field = request.POST.get('name')
        if field in allowedFields:
            val = request.POST.get('value')
            val = sanitize_html(val)
            setattr(instance, field, val)
            instance.save(update_fields=[field])
            if hasattr(instance, "invalidate_cache"):
                instance.invalidate_cache()
            if model == Paper:
                merged = instance.recompute_fingerprint_and_merge_if_needed()
                response['merged'] = ''
                if merged:
                    response['merged'] = merged.pk
                    response['merged_title'] = merged.title
            response['status'] = 'OK'
            response['value'] = val
            return HttpResponse(json.dumps(response), content_type='text/plain')
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponseNotFound(json.dumps(response), content_type='text/plain')

# Researcher management
@user_passes_test(is_admin)
def deleteResearcher(request, pk):
    researcher = get_object_or_404(Researcher, pk=pk)
    researcher.delete()
    return HttpResponse('OK', content_type='text/plain')

def researcherCandidatesByName(name):
    """
    Given a Name object, find researchers that are potentially meant
    by this name. They come either from the model (Researcher instances
    who have this name as NameVariant) or search results from the ORCID
    API that are compatible with this name.

    Results are returned as a list of HTML elements, to be displayed
    in the disambiguation dialog.
    """
    # From the model
    related_researchers = list(map(lambda nv: nv.researcher, name.namevariant_set.all()))
    def renderResearcher(res):
        return loader.render_to_string('papers/itemResearcher.html',
                {'researcher':res})
    rendered = map(renderResearcher, related_researchers)

    # From ORCID
    related_orcids = OrcidProfile.search_by_name(name.first, name.last)
    def renderProfile(res):
        rendered_keywords = ', '.join(res.get('keywords',[]))
        res['rendered_keywords'] = rendered_keywords
        return loader.render_to_string('papers/itemOrcid.html',
                {'profile':res})
    rendered += map(renderProfile, related_orcids)
    return rendered
    

def newUnaffiliatedResearcher(request):
    if request.method != 'POST':
        return HttpResponseForbidden('"Invalid method"', content_type='application/javascript')
    form = AddUnaffiliatedResearcherForm(request.POST)
    researcher = None
    if form.is_valid():
        orcid = form.cleaned_data['orcid']
        if orcid:
            researcher = Researcher.get_or_create_by_orcid(orcid)
        else:
            first = form.cleaned_data['first']
            last = form.cleaned_data['last']
            # Check that the researcher is not already known under a different name.
            if not form.cleaned_data.get('force'):
                name, created = Name.get_or_create(first, last)
                try:
                    researcher = Researcher.objects.get(name=name)
                    return HttpResponse(json.dumps({'url':researcher.url}))
                except (Researcher.DoesNotExist, MultipleObjectsReturned):
                    pass
                candidates = researcherCandidatesByName(name)
                if candidates:
                    return HttpResponse(json.dumps({'disambiguation':candidates}))

            researcher = Researcher.get_or_create_by_name(first, last)
        researcher.fetch_everything_if_outdated()
        return HttpResponse(json.dumps({'url':researcher.url}))
    else:
        return HttpResponseForbidden(json.dumps(form.errors), content_type='application/javascript')


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

            try:
                researcher = Researcher.create_from_scratch(first, last, dept, email, role, homepage)
            except ValueError:
                return HttpResponseForbidden('Researcher already present', content_type='text/plain')

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
@user_passes_test(is_authenticated)
def annotatePaper(request, pk, status):
    paper = get_object_or_404(Paper, pk=pk)
    try:
        status = int(status)
        if not status in range(len(VISIBILITY_CHOICES)):
            raise ValueError
    except ValueError:
        return HttpResponseForbidden('Invalid visibility status', content_type='text/plain')

    visibility = VISIBILITY_CHOICES[status][0]
    Annotation.create(paper, visibility, request.user)
    return HttpResponse('OK', content_type='text/plain')

@user_passes_test(is_authenticated)
def changePaper(request):
    allowedFields = ['title']
    return process_ajax_change(request, Paper, allowedFields)

# Department management
@user_passes_test(is_authenticated)
def changeDepartment(request):
    allowedFields = ['name']
    return process_ajax_change(request, Department, allowedFields)

# Researcher management
@user_passes_test(is_authenticated)
def changeResearcher(request):
    allowedFields = ['role']
    return process_ajax_change(request, Researcher, allowedFields)

def harvestingStatus(request, pk): 
    researcher = get_object_or_404(Researcher, pk=pk)
    resp = {}
    if researcher.current_task:
        resp['status'] = researcher.current_task
        resp['display'] = researcher.get_current_task_display()
    else:
        resp = None
    return HttpResponse(json.dumps(resp), content_type='text/json')

@user_passes_test(is_authenticated)
def waitForConsolidatedField(request):
    try:
        paper = Paper.objects.get(pk=int(request.GET["id"]))
    except (KeyError, ValueError, Paper.DoesNotExist):
        return HttpResponseForbidden('Invalid paper id', content_type='text/plain')
    field = request.GET.get('field')
    value = None
    success = None
    paper.consolidate_metadata(wait=True)
    if field == 'abstract':
        value = kill_html(paper.abstract)
        success = len(paper.abstract) > 64
    else:
        return HttpResponseForbidden('Invalid field', content_type='text/plain')
    return HttpResponse(json.dumps({'value':value}), content_type='text/json')

# Author management
@user_passes_test(is_authenticated)
def changeAuthor(request):
    response = dict()
    try:
        author = Author.objects.get(pk=request.POST.get('pk'))
        first = request.POST.get('value[first]')
        if first:
            first = sanitize_html(first)
        last = request.POST.get('value[last]')
        if last:
            last = sanitize_html(last)
        if not first or not last:
            return HttpResponseForbidden('First and last names are required.', content_type='text/plain')
        if author.name.first != first or author.name.last != last:
            new_name = Name.lookup_name((first,last))
            new_name.save()
            author.name_id = new_name.pk
            author.save()

        author.paper.invalidate_cache()
        response['status'] = 'OK'
        researcher_id = author.researcher_id
        if not researcher_id:
            researcher_id = False
        response['value'] = {'first':first,'last':last,'researcher_id':researcher_id}
        
        # The fingerprint might have changed and might collide with another paper
        merged = author.paper.recompute_fingerprint_and_merge_if_needed()
        response['merged'] = ''
        if merged:
            response['merged'] = merged.pk
            response['merged_title'] = merged.title

        return HttpResponse(json.dumps(response), content_type='text/plain')
    except ObjectDoesNotExist:
        return HttpResponseNotFound(json.dumps(response), content_type='text/plain')

   

# Publisher management
@user_passes_test(is_admin)
def changePublisherStatus(request):
    allowedStatuses = [s[0] for s in OA_STATUS_CHOICES]
    try:
        pk = request.POST.get('pk')
        publisher = Publisher.objects.get(pk=pk)
        status = request.POST.get('status')
        if status in allowedStatuses and status != publisher.oa_status:
            send_task('change_publisher_oa_status', [], {'pk':pk,'status':status})
            return HttpResponse('OK', content_type='text/plain')
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponseNotFound('NOK: '+message, content_type='text/plain')

urlpatterns = patterns('',
#    url(r'^annotate-paper-(?P<pk>\d+)-(?P<status>\d+)$', annotatePaper, name='ajax-annotatePaper'),
#    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-deleteResearcher'),
#    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
#    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
#    url(r'^change-researcher$', changeResearcher, name='ajax-changeResearcher'),
#    url(r'^change-author$', changeAuthor, name='ajax-changeAuthor'),
#    url(r'^add-researcher$', addResearcher, name='ajax-addResearcher'),
    url(r'^new-unaffiliated-researcher$', newUnaffiliatedResearcher, name='ajax-newUnaffiliatedResearcher'),
    url(r'^change-publisher-status$', changePublisherStatus, name='ajax-changePublisherStatus'),
    url(r'^harvesting-status-(?P<pk>\d+)$', harvestingStatus, name='ajax-harvestingStatus'),
    url(r'^wait-for-consolidated-field$', waitForConsolidatedField, name='ajax-waitForConsolidatedField'),
)

