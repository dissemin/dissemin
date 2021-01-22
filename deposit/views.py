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
import os

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_form
from datetime import date
from jsonview.decorators import json_view
from ratelimit.decorators import ratelimit

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.http import HttpResponseForbidden
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import View
from django.views.generic import ListView
from django.views.generic.edit import FormView

from deposit.declaration import get_declaration_pdf
from deposit.decorators import shib_meta_to_user
from deposit.forms import PaperDepositForm
from deposit.forms import UserPreferencesForm
from deposit.models import DepositRecord
from deposit.models import Repository
from deposit.models import UserPreferences
from deposit.utils import get_preselected_repository
from papers.models import Paper
from papers.user import is_authenticated

logger = logging.getLogger('dissemin.' + __name__)

def get_all_repositories_and_protocols(paper, user):
    """
    Gets all enabled repositories together with their protocols.
    :param paper: The paper to be deposited
    :param user: The user who wnats to deposit
    :return: List of tupels containing each a pair of a repository and its protocol.
    """
    repositories = Repository.objects.filter(enabled=True)
    protocols = []
    for r in repositories:
        implem = r.protocol_for_deposit(paper, user)
        if implem is not None:
            protocols.append((r, implem))
    return protocols


@json_view
@user_passes_test(is_authenticated)
@shib_meta_to_user
def get_metadata_form(request):
    repo = get_object_or_404(Repository, pk=request.GET.get('repository'))
    if not repo.enabled:
        return HttpResponseForbidden(_('This repository is currently not enabled.'))
    paper = get_object_or_404(Paper, pk=request.GET.get('paper'))
    protocol = repo.protocol_for_deposit(paper, request.user)
    if protocol is None:
        logger.warning("No protocol")
        return {'status': 'repoNotAvailable',
                'message': _('This repository is not available for this paper.')}

    form = protocol.get_form()
    return {'status': 'success',
            'form': as_crispy_form(form)}


@user_passes_test(is_authenticated)
@shib_meta_to_user
def start_view(request, pk):
    paper = get_object_or_404(
        Paper.objects.prefetch_related(
            'oairecord_set'
        ),
        pk=pk
    )
    repositories_protocol = get_all_repositories_and_protocols(paper, request.user)
    used_protocols = set([proto for repo, proto in repositories_protocol])
    available_repositories = sorted([repo for repo, proto in repositories_protocol], key=lambda r: r.name.lower())
    
    # select the most appropriate repository
    preselected_repository = get_preselected_repository(request.user, available_repositories)
    preselected_protocol = None
    if preselected_repository:
        preselected_protocol = {repo.id : proto for repo, proto in repositories_protocol}.get(preselected_repository.id, None)
    elif len(repositories_protocol) > 0:
        preselected_repository = repositories_protocol[0][0]
        preselected_protocol = repositories_protocol[0][1]

    breadcrumbs = paper.breadcrumbs()
    breadcrumbs.append((_('Deposit'), ''))
    context = {
        'paper': paper,
        'max_file_size': settings.DEPOSIT_MAX_FILE_SIZE,
        'available_repositories': available_repositories,
        'selected_repository': preselected_repository,
        'selected_protocol': preselected_protocol,
        'is_owner': paper.is_owned_by(request.user, flexible=True),
        'breadcrumbs': breadcrumbs,
        'repositoryForm': None,
        'paper_form': PaperDepositForm(
            initial={
                'radioUploadType' : request.GET.get('type')
            }
        ),
        'collapse_doctype' : request.GET.get('type') in ['preprint', 'postprint', 'pdfversion'],
        'used_protocols' : used_protocols,
    }
    return render(request, 'deposit/start.html', context)


class MyDepositsView(LoginRequiredMixin, ListView):
    """
    A few to list all publications of a given user
    """

    context_object_name = 'deposits'
    template_name = 'deposit/deposits.html'

    def get_queryset(self):
        """
        Fetch all deposition of the user, with depending objects
        """
        deposits = DepositRecord.objects.filter(
            user=self.request.user,
            identifier__isnull=False
        ).order_by(
            '-date'
        ).select_related(
            'license',
            'oairecord',
            'paper',
            'repository',
        )

        return deposits



class GlobalPreferencesView(LoginRequiredMixin, FormView):
    """
    View to handle the form with global repository settings
    """

    form_class = UserPreferencesForm
    model = UserPreferences
    success_url = reverse_lazy('preferences-global')
    template_name = 'deposit/preferences_global.html'

    def form_valid(self, form):
        """
        If the form is valid, save it and return to success page
        """
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        For the navbar, we add the enabled repositories as context
        """
        context = super().get_context_data(**kwargs)
        context['repositories'] = Repository.objects.filter(enabled=True)

        return context

    def get_form_kwargs(self):
        """
        We pass an instance of the model
        """
        form_kwargs = super().get_form_kwargs()
        form_kwargs['instance'] = UserPreferences.get_by_user(self.request.user)

        return form_kwargs


class RepositoryPreferencesView(LoginRequiredMixin, FormView):
    """
    View to handle form of each repository having such
    """

    template_name = 'deposit/preferences_repository.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.repository = get_object_or_404(Repository, pk=kwargs.get('pk'))
        self.protocol = self.repository.get_implementation()
        if not self.protocol:
            raise Http404(_('This repository could not be found.'))

    def form_valid(self, form):
        """
        If the form is valid, save it and return to success page
        """
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        For the navbar, we add the enabled repositories as context
        """
        print(self.kwargs)
        context = super().get_context_data(**kwargs)
        context['repository'] = self.repository
        context['repositories'] = Repository.objects.filter(enabled=True)

        return context

    def get_form_class(self):
        return self.protocol.preferences_form_class

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['instance'] = self.protocol.get_preferences(self.request.user)

        return form_kwargs

    def get_success_url(self):
        return reverse('preferences-repository', args=[self.repository.pk, ])


@require_POST
@json_view
@user_passes_test(is_authenticated)
@shib_meta_to_user
@ratelimit(key='ip', rate='200/d')
def submitDeposit(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    context = {'status': 'error'}
    form = PaperDepositForm(data=request.POST)
    if not form.is_valid():
        context['form'] = form.errors
        context['message'] = _("Not all fields have been filled correctly.")
        return context, 400

    # This validation could take place in the form (but we need access to the
    # paper and user?)
    repository = form.cleaned_data['radioRepository']
    protocol = repository.protocol_for_deposit(paper, request.user)
    if protocol is None:
        context['radioRepository'] = _(
            "This repository cannot be used for this paper.")
        return context, 400

    repositoryForm = protocol.get_bound_form(request.POST)

    if not repositoryForm.is_valid():
        context['form_html'] = as_crispy_form(repositoryForm)
        context['message'] = _("Not all fields have been filled correctly.")
        return context, 400

    # Store the repository as in the user preferences
    userprefs = UserPreferences.get_by_user(request.user)
    userprefs.last_repository = repository
    userprefs.save(update_fields=['last_repository'])

    # Check that the paper has been uploaded by the same user
    pdf = form.cleaned_data['file_id']
    if pdf.user != request.user:
        context['message'] = _('Access to the PDF was denied.')
        return context, 400

    # Submit the paper to the repository
    path = os.path.join(settings.MEDIA_ROOT, pdf.file.name)

    # Create initial record
    d = DepositRecord(
            paper=paper,
            user=pdf.user,
            repository=repository,
            upload_type=form.cleaned_data['radioUploadType'],
            file=pdf)
    d.save()

    submitResult = protocol.submit_deposit_wrapper(path, repositoryForm)

    d.request = submitResult.logs
    if submitResult.status == 'failed':
        context['message'] = submitResult.message
        d.save()
        # Send the failed deposit as error to sentry
        msg = "Deposit failed for id %s for paper %s \n\n" % (d.pk, paper.pk)
        logger.error(msg + submitResult.logs)
        return context, 400

    d.identifier = submitResult.identifier
    d.additional_info = submitResult.additional_info
    d.status = submitResult.status
    d.oairecord = submitResult.oairecord
    d.license = submitResult.license
    d.pub_date = submitResult.embargo_date
    if d.pub_date is None and d.status == 'published':
        d.pub_date = date.today()
    d.save()
    paper.update_availability()
    paper.save()
    paper.update_index()

    context['status'] = 'success'
    # TODO change this (we don't need it)
    context['upload_id'] = d.id
    return context


class LetterDeclarationView(LoginRequiredMixin, View):
    """
    View to return a test file. The user must be logged in and must have access to the deposit.
    """

    def get(self, request, pk):
        """
        We test if the user is the user that own the deposit and return a PDF file if the repository specifies this
        """
        dr = get_object_or_404(DepositRecord.objects.select_related('paper', 'repository', 'repository__letter_declaration', 'user', 'license'), pk=pk)

        if dr.user != request.user:
            raise PermissionDenied
        # If the repository requires a letter of declaration, we try to create the pdf, otherwise we return 404.
        if dr.repository.letter_declaration is not None and dr.status == "pending":
            # URL get precendence over pdf
            if dr.repository.letter_declaration.url:
                return redirect(dr.repository.letter_declaration.url)
            else:
                pdf = get_declaration_pdf(dr)
                pdf.seek(0)
                filename = _("Declaration {}.pdf").format(dr.paper.slug[:25])
                return FileResponse(pdf, as_attachment=True, filename=filename)
        else:
            raise Http404(_("No pdf found for dr {}".format(dr.pk)))
