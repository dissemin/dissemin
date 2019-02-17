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



from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views import generic
from haystack.generic_views import SearchView
from publishers.forms import PublisherForm
from publishers.models import OA_STATUS_CHOICES
from publishers.models import Publisher
from publishers.models import publishers_breadcrumbs
from search import SearchQuerySet

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


class SlugDetailView(generic.DetailView):
    """
    A DetailView for objects with a slug field for human-friendly URLs:
    redirects if the slug in the request does not match the object's slug.
    """
    view_name = None

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if kwargs.get('slug') == self.object.slug:
            context = self.get_context_data(object=self.object, **kwargs)
            return self.render_to_response(context)
        else:
            kwargs['slug'] = self.object.slug
            return self.redirect(**kwargs)

    def redirect(self, **kwargs):
        return redirect(self.view_name, permanent=True, **kwargs)


class PublishersView(SearchView):
    paginate_by = NB_RESULTS_PER_PAGE
    template_name = 'publishers/list.html'
    form_class = PublisherForm
    queryset = SearchQuerySet().models(Publisher)

    def get_form_kwargs(self):
        """
        We make sure the search is valid even if no parameter
        was passed, in which case we add a default empty query.
        Otherwise the search form is not bound and search fails.
        """
        args = super(PublishersView, self).get_form_kwargs()
        if 'data' not in args:
            args['data'] = {self.search_field:''}
        return args


    def get_context_data(self, **kwargs):
        context = super(PublishersView, self).get_context_data(**kwargs)

        context['search_description'] = _('Publishers')
        context['nb_results'] = self.queryset.count()
        context['breadcrumbs'] = publishers_breadcrumbs()
        context['oa_desc'] = dict([(s[0], s[2]) for s in OA_STATUS_CHOICES])

        return context


class PublisherView(SlugDetailView):
    model = Publisher
    template_name = 'publishers/policy.html'
    view_name = 'publisher'

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
