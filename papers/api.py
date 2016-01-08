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
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, Http404, JsonResponse
import json, requests
from jsonview.decorators import json_view

from papers.models import *

from rest_framework import serializers, routers, viewsets, views
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer

class JsonSerializer(serializers.BaseSerializer):
    def to_representation(self, obj):
        return obj.json()

#class PaperViewSet(viewsets.ReadOnlyModelViewSet):
#    queryset = Paper.objects.filter(visibility='VISIBLE')
#    serializer_class = JsonSerializer

class PaperViewSet(viewsets.ViewSet):
#    def list(self, request, format=None):
#        return Response([])
    permission_classes = (AllowAny,)

    def retrieve(self, request, pk, format=None):
        """
        Get the metadata associated with a paper
        """
        paper = get_object_or_404(Paper, pk=pk)
        serializer = JsonSerializer(paper)
        return Response(serializer.data)

    #serializer.data)

router = routers.DefaultRouter()
router.register(r'papers', PaperViewSet, base_name='papers')

#@api_view
#def api_paper(request, pk):
#    paper = get_object_or_404(Paper, pk=pk)
#    return Response({
#            'status':'ok',
#            'id':pk,
#            'paper':paper.json()
#            })

#@api_view
#def api_root(request, format=None):
#    return Response({
#        'papers': reverse
#        })

@json_view
def api_paper_doi(request, doi):
    p = Paper.create_by_doi(doi, bare=True)
    if p is None:
        raise Http404
    return {
            'status':'ok',
            'paper':p.json()
            }

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
#    url(r'^paper/(?P<pk>\d+)/$', PaperView.as_view(), name='api-paper'),
    url(r'^(?P<doi>10\..*)$', api_paper_doi, name='api-paper-doi'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
)

