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

from django.conf.urls import include, url
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden, Http404, JsonResponse
import json, requests
from jsonview.decorators import json_view
from jsonview.exceptions import BadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from papers.models import *
from papers.name import parse_comma_name
from papers.utils import tolerant_datestamp_to_datetime
from papers.errors import MetadataSourceException

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
        raise Http404("The paper you requested could not be found.")
    return {
            'status':'ok',
            'paper':p.json()
            }

@json_view
@csrf_exempt
@require_POST
def api_paper_query(request):
    try:
        fields = json.loads(request.body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        raise BadRequest('Invalid JSON payload')

    doi = fields.get('doi')
    if doi:
        p = None
        try:
            p = Paper.create_by_doi(doi, bare=True)
        except MetadataSourceException:
            pass
        if p is None:
            raise BadRequest('Could not find a paper with this DOI')
        return {'status':'ok','paper':p.json()}

    title = fields.get('title')
    if type(title) != unicode or not title or len(title) > 512:
        raise BadRequest('Invalid title, has to be a non-empty string shorter than 512 characters')

    pubdate = fields.get('date')

    date = fields.get('date')
    if type(date) != unicode:
        raise BadRequest('A date is required')
    try:
        date = tolerant_datestamp_to_datetime(date)
    except ValueError as e:
        raise BadRequest(unicode(e))

    authors = fields.get('authors')
    if type(authors) != list:
        raise BadRequest('A list of authors is expected')

    parsed_authors = []
    for a in authors:
        author = None
        if type(a) != dict:
            raise BadRequest('Invalid author')

        if 'first' in a and 'last' in a:
            if type(a['first']) != unicode or type(a['last']) != unicode or not a['last']:
                raise BadRequest('Invalid (first,last) name provided')
            else:
                author = (a['first'],a['last'])
        elif 'plain' in a:
            if type(a['plain']) != unicode or not a['plain']:
                raise BadRequest('Invalid plain name provided')
            else:
                author = parse_comma_name(a['plain'])

        if author is None:
            raise BadRequest('Invalid author')

        parsed_authors.append(BareName.create(author[0],author[1]))

    if not authors:
        raise BadRequest('No authors provided')

    try:
        p = BarePaper.create(title, parsed_authors, date)
    except ValueError:
        raise BadRequest('Invalid paper')
    import backend.oai as oai

    return {'status':'ok','paper':p.json()}


urlpatterns = [
    url(r'^', include(router.urls)),
#    url(r'^paper/(?P<pk>\d+)/$', PaperView.as_view(), name='api-paper'),
    url(r'^(?P<doi>10\..*)$', api_paper_doi, name='api-paper-doi'),
    url(r'^query$', api_paper_query, name='api-paper-query'),
#    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
#    url(r'^docs/', include('rest_framework_swagger.urls')),
]

