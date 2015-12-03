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
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, Http404
import json, requests

from papers.models import *

from jsonview.decorators import json_view

@json_view
def api_paper(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    return {
            'status':'ok',
            'id':pk,
            'paper':paper.json()
            }

@json_view
def api_paper_doi(request, doi):
    p = Paper.create_by_doi(doi)
    if p is None:
        raise Http404
    return {
            'status':'ok',
            'id':p.pk,
            'paper':p.json()
            }

urlpatterns = patterns('',
    url(r'^paper/(?P<pk>\d+)/$', api_paper, name='api-paper'),
    url(r'^(?P<doi>10\..*)$', api_paper_doi, name='api-paper-doi'),
)

