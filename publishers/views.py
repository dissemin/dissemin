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

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import generic
from django.utils.translation import ugettext as _
from dissemin.settings import UNIVERSITY_BRANDING

from publishers.models import *

# Number of publishers per page in the publishers list
NB_RESULTS_PER_PAGE = 20 
# Number of journals per page on a Publisher page
NB_JOURNALS_PER_PAGE = 30

def varyQueryArguments(key, args, possibleValues):
    variants = []
    for s in possibleValues:
        queryargs = args.copy()
        if s[0] != queryargs.get(key):
            queryargs[key] = s[0]
        else:
            queryargs.pop(key)
        variants.append(s+(queryargs,))
    return variants


def publishersView(request, **kwargs):
    context = dict()
    # Build the queryset
    queryset = Publisher.objects.filter(stats__isnull=False)
    args = request.GET.copy()
    args.update(kwargs)

    search_description = _('Publishers')
    if 'status' in args:
        queryset = queryset.filter(oa_status=args.get('status'))
        context['status'] = args.get('status')

    # Ordering
    # queryset = queryset.order_by('name')
    queryset = queryset.order_by('-stats__num_tot')
    queryset = queryset.select_related('stats')

    # Build the paginator
    paginator = Paginator(queryset, NB_RESULTS_PER_PAGE)
    page = args.get('page')
    try:
        current_publishers = paginator.page(page)
    except PageNotAnInteger:
        current_publishers = paginator.page(1)
    except EmptyPage:
        current_publishers = paginator.page(paginator.num_pages)

    context['search_results'] = current_publishers
    context['search_description'] = search_description
    context['nb_results'] = queryset.count()
    context['breadcrumbs'] = publishers_breadcrumbs()

    # Build the GET requests for variants of the parameters
    args_without_page = args.copy()
    if 'page' in args_without_page:
        del args_without_page['page']
    oa_variants = varyQueryArguments('status', args_without_page, OA_STATUS_CHOICES)

    context['oa_status_choices'] = oa_variants
    context.update(UNIVERSITY_BRANDING)
    return render(request, 'publishers/list.html', context)

class PublisherView(generic.DetailView):
    model = Publisher
    template_name = 'publishers/policy.html'
    def get_context_data(self, **kwargs):
        context = super(PublisherView, self).get_context_data(**kwargs)
        context['oa_status_choices'] = OA_STATUS_CHOICES
        # Build the paginator
        publisher = context['publisher']
        paginator = Paginator(publisher.sorted_journals, NB_JOURNALS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            current_journals = paginator.page(page)
        except PageNotAnInteger:
            current_journals = paginator.page(1)
        except EmptyPage:
            current_journals = paginator.page(paginator.num_pages)
        context['journals'] = current_journals
        
        # Breadcrumbs
        context['breadcrumbs'] = publisher.breadcrumbs()
        
        return context


