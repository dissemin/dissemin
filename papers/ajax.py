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

import logging

from celery.exceptions import TimeoutError
from djgeojson.views import GeoJSONLayerView
from functools import wraps
from jsonview.decorators import json_view

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from papers.models import Paper
from papers.models import Researcher
from papers.models import Institution
from papers.user import is_admin
from papers.user import is_authenticated
from papers.utils import kill_html
from papers.utils import sanitize_html


logger = logging.getLogger('dissemin.' + __name__)


def login_required_ajax(function):
    """
    Decorator that sends 401 as response to not authenticated ajax request
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)
        return _wrapper_func

    return decorator(function)


def ajax_required(function):
    """
    Decorator that sends 400 as response if not an ajax request
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapper_func(request, *args, **kwargs):
            if request.is_ajax():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=400)
        return _wrapper_func
    return decorator(function)


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
            if isinstance(val, str):
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

# paper management
#@user_passes_test(is_admin)
# def changepaper(request):
#    allowedFields = ['title']
#    return process_ajax_change(request, Paper, allowedFields)

# department management
#@user_passes_test(is_admin)
# def changedepartment(request):
#    allowedFields = ['name']
#    return process_ajax_change(request, Department, allowedFields)

# researcher management
#@user_passes_test(is_admin)
# def changeresearcher(request):
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
@require_POST
def claimPaper(request):
    """claim paper pk for current user"""
    success = False
    try:
        paper = Paper.objects.get(pk=int(request.POST["pk"]))
    except (KeyError, ValueError, Paper.DoesNotExist):
        return {'success': success, 'message': 'Invalid paper id'}, 404
    try:
        # returns true or false depending on whether something was actually
        # changed
        paper.claim_for(request.user)
    except ValueError:
        # paper cannot be claimed
        return {'success': success,
                'message': 'Paper cannot be claimed by user'}, 403
    success = True
    return {'success': success}


@user_passes_test(is_authenticated)
@json_view
@require_POST
def unclaimPaper(request):
    """unclaim paper pk for current user"""
    success = False
    try:
        paper = Paper.objects.get(pk=int(request.POST["pk"]))
    except (KeyError, ValueError, Paper.DoesNotExist):
        return {'success': success, 'message': 'Invalid paper id'}, 404
    # returns true or false depending on whether something was actually changed
    success = paper.unclaim_for(request.user)
    return {'success': success}


@user_passes_test(is_authenticated)
@json_view
def waitForConsolidatedField(request):
    success = False
    try:
        paper = Paper.objects.get(pk=int(request.GET["id"]))
    except (KeyError, ValueError, Paper.DoesNotExist):
        return {'success': success, 'message': 'Invalid paper id'}, 404
    field = request.GET.get('field')
    value = None
    try:
        paper.consolidate_metadata(wait=True)
    except TimeoutError:
        # Zotero instance is down / slow / failing, consolidation failed. Not
        # a big deal.
        pass
    if field == 'abstract':
        value = kill_html(paper.abstract)
        success = len(paper.abstract) > 64
    else:
        return {'success': success, 'message': 'Invalid field'}, 401
    return {'success': success, 'value': value}


@login_required_ajax
@ajax_required
@json_view
@require_POST
def todo_list_add(request):
    """
    Adds a paper from a users todolist
    """
    body = {
        'success_msg' : _('Remove from to-do list'),
        'error_msg' : _('Marking failed'),
        'data-action': 'unmark',
    }
    paper_pk = request.POST.get('paper_pk', None)
    if paper_pk is None:
        return body, 400
    try:
        paper = Paper.objects.get(pk=int(paper_pk))
    except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
        return body, 404

    try:
        paper.todolist.add(request.user)
    except Exception as e:
        logger.exception(e)
        return body, 500

    return body, 200


@login_required_ajax
@ajax_required
@json_view
@require_POST
def todo_list_remove(request):
    """
    Removes a paper from a users todolist
    """
    body = {
        'success_msg' : _('Mark for later upload'),
        'error_msg' : _('Removing failed'),
        'data-action': 'mark',
    }
    paper_pk = request.POST.get('paper_pk', None)
    if paper_pk is None:
        return body, 400
    try:
        paper = Paper.objects.get(pk=int(paper_pk))
    except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
        return body, 404

    try:
        paper.todolist.remove(request.user)
    except Exception as e:
        logger.exception(e)
        return body, 500

    return body, 200


# author management
#@user_passes_test(is_admin)
#@json_view
# def changeAuthor(request):
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


class InstitutionsMapView(GeoJSONLayerView):
    model = Institution
    geometry_field = 'coords'

    def get_queryset(self):
        return Institution.objects.filter(coords__isnull=False)
