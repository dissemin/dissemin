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
from django.views.decorators.http import require_POST
from django.template import loader
from django.forms import ValidationError
from django.db import IntegrityError
from django.utils.translation import ugettext as __
import json, requests

from django.views.decorators.csrf import csrf_exempt
from celery.execute import send_task

from dissemin.settings import URL_DEPOSIT_DOWNLOAD_TIMEOUT, DEPOSIT_MAX_FILE_SIZE, MEDIA_ROOT

from papers.models import *
from papers.user import *
from papers.forms import AddUnaffiliatedResearcherForm
from papers.utils import iunaccent, sanitize_html, kill_html
from papers.name import normalize_name_words

from jsonview.decorators import json_view

import os.path

@json_view
@require_POST
def process_ajax_change(request, model, allowedFields):
    """
    General function used to change a CharField in a model with ajax
    """
    response = dict()
    try:
        instance = model.objects.get(pk=request.POST.get('pk'))
        field = request.POST.get('name')
        if field in allowedFields:
            val = request.POST.get('value')
            # TODO check that 'value' is actually present
            if type(val) == type(''):
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
            return response
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return response, 404

# Researcher management
@user_passes_test(is_admin)
def deleteResearcher(request, pk):
    """
    Deletes a researcher (from a department). Their papers are
    left as they are.
    """
    researcher = get_object_or_404(Researcher, pk=pk)
    dept = researcher.department
    researcher.delete()
    if dept:
        dept.update_stats()
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
    seen_orcids = set()
    for researcher in related_researchers:
        if researcher.orcid:
            seen_orcids.add(researcher.orcid)
    rendered = map(renderResearcher, related_researchers)

    # From ORCID
    related_orcids = OrcidProfile.search_by_name(name.first, name.last)
    def renderProfile(res):
        rendered_keywords = ', '.join(res.get('keywords',[]))
        res['rendered_keywords'] = rendered_keywords
        return loader.render_to_string('papers/itemOrcid.html',
                {'profile':res})
    related_orcids = filter(lambda r: r['orcid'] not in seen_orcids, related_orcids)
    rendered += map(renderProfile, related_orcids)
    return rendered
    
@json_view
@require_POST
def newUnaffiliatedResearcher(request):
    """
    creates a new unaffiliated researcher, or returns
    a list of possible candidates if the name matches known
    profiles.
    """
    form = AddUnaffiliatedResearcherForm(request.POST)
    researcher = None
    if form.is_valid():
        first = normalize_name_words(form.cleaned_data['first'])
        last = normalize_name_words(form.cleaned_data['last'])
        # Check that the researcher is not already known under a different name.
        if not form.cleaned_data.get('force'):
            name, created = Name.get_or_create(first, last)
            candidates = researcherCandidatesByName(name)
            if candidates:
                return {'disambiguation':candidates}

        researcher = Researcher.create_by_name(first, last)
        researcher.fetch_everything_if_outdated()
        return {'url':researcher.url}
    else:
        return form.errors, 403

# paper management
#@user_passes_test(is_authenticated)
#def annotatepaper(request, pk, status):
#    paper = get_object_or_404(Paper, pk=pk)
#    try:
#        status = int(status)
#        if not status in range(len(VISIBILITY_CHOICES)):
#            raise ValueError
#    except valueError:
#        return HttpResponseForbidden('Invalid visibility status', content_type='text/plain')
#
#    visibility = VISIBILITY_CHOICES[status][0]
#    annotation.create(paper, visibility, request.user)
#    return httpResponse('OK', content_type='text/plain')

#@user_passes_test(is_admin)
#def changepaper(request):
#    allowedFields = ['title']
#    return process_ajax_change(request, Paper, allowedFields)

# department management
#@user_passes_test(is_admin)
#def changedepartment(request):
#    allowedFields = ['name']
#    return process_ajax_change(request, Department, allowedFields)

# researcher management
#@user_passes_test(is_admin)
#def changeresearcher(request):
#    allowedFields = ['role']
#    return process_ajax_change(request, Researcher, allowedFields)

@user_passes_test(is_admin)
def setResearcherDepartment(request):
    allowedFields = ['department_id']
    return process_ajax_change(request, Researcher, allowedFields)

@json_view
def harvestingStatus(request, pk): 
    researcher = get_object_or_404(Researcher, pk=pk)
    resp = {}
    if researcher.current_task:
        resp['status'] = researcher.current_task
        resp['display'] = researcher.get_current_task_display()
    else:
        resp = None
    return resp

@user_passes_test(is_authenticated)
@json_view
def waitForConsolidatedField(request):
    try:
        paper = Paper.objects.get(pk=int(request.GET["id"]))
    except (KeyError, ValueError, Paper.DoesNotExist):
        return HttpResponseForbidden('Invalid paper id', content_type='text/plain')
    field = request.GET.get('field')
    value = None
    success = False
    paper.consolidate_metadata(wait=True)
    if field == 'abstract':
        value = kill_html(paper.abstract)
        success = len(paper.abstract) > 64
    else:
        return {'success':success,'message':'Invalid field'}
    return {'success':success,'value':value}

# author management
#@user_passes_test(is_admin)
#@json_view
#def changeAuthor(request):
#    response = dict()
#    try:
#        author = Author.objects.get(pk=request.POST.get('pk'))
#        first = request.POST.get('value[first]')
#        if first:
#            first = sanitize_html(first)
#        last = request.POST.get('value[last]')
#        if last:
#            last = sanitize_html(last)
#        if not first or not last:
#            return {'message':'First and last names are required.'}, 403
#        if author.name.first != first or author.name.last != last:
#            new_name = Name.lookup_name((first,last))
#            new_name.save()
#            author.name_id = new_name.pk
#            author.save()
#
#        author.paper.invalidate_cache()
#        response['status'] = 'OK'
#        researcher_id = author.researcher_id
#        if not researcher_id:
#            researcher_id = False
#        response['value'] = {'first':first,'last':last,'researcher_id':researcher_id}
#        
#        # the fingerprint might have changed and might collide with another paper
#        merged = author.paper.recompute_fingerprint_and_merge_if_needed()
#        response['merged'] = ''
#        if merged:
#            response['merged'] = merged.pk
#            response['merged_title'] = merged.title
#
#        return response
#    except ObjectDoesNotExist:
#        return response, 404

# Publisher management
@user_passes_test(is_admin)
@require_POST
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
    url(r'^delete-researcher-(?P<pk>\d+)$', deleteResearcher, name='ajax-deleteResearcher'),
#    url(r'^change-department$', changeDepartment, name='ajax-changeDepartment'),
#    url(r'^change-paper$', changePaper, name='ajax-changePaper'),
#    url(r'^change-researcher$', changeResearcher, name='ajax-changeResearcher'),
#    url(r'^change-author$', changeAuthor, name='ajax-changeAuthor'),
    url(r'^new-unaffiliated-researcher$', newUnaffiliatedResearcher, name='ajax-newUnaffiliatedResearcher'),
    url(r'^change-publisher-status$', changePublisherStatus, name='ajax-changePublisherStatus'),
#    url(r'^harvesting-status-(?P<pk>\d+)$', harvestingStatus, name='ajax-harvestingStatus'),
    url(r'^wait-for-consolidated-field$', waitForConsolidatedField, name='ajax-waitForConsolidatedField'),
    url(r'^set-researcher-department$', setResearcherDepartment, name='ajax-setResearcherDepartment'),
)

