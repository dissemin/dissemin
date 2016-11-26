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

import os

from crispy_forms.templatetags.crispy_forms_filters import as_crispy_form
from crispy_forms.utils import render_crispy_form
from deposit.forms import PaperDepositForm
from deposit.models import DepositRecord
from deposit.models import Repository
from dissemin.settings import DEPOSIT_MAX_FILE_SIZE
from dissemin.settings import MEDIA_ROOT
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from jsonview.decorators import json_view
from papers.models import Paper
from papers.user import is_authenticated


def get_all_repositories_and_protocols(paper, user):
    repositories = Repository.objects.all()
    protocols = []
    for r in repositories:
        implem = r.protocol_for_deposit(paper, user)
        # if implem is not None:
        protocols.append((r, implem))
    return protocols


@json_view
@user_passes_test(is_authenticated)
def get_metadata_form(request):
    paper = get_object_or_404(Paper, pk=request.GET.get('paper'))
    repo = get_object_or_404(Repository, pk=request.GET.get('repository'))
    protocol = repo.protocol_for_deposit(paper, request.user)
    if protocol is None:
        print "no protocol"
        return {'status': 'repoNotAvailable',
                'message': _('This repository is not available for this paper.')}

    form = protocol.get_form()
    return {'status': 'success',
            'form': as_crispy_form(form)}


@user_passes_test(is_authenticated)
def start_view(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    repositories = get_all_repositories_and_protocols(paper, request.user)
    selected_repository = None
    selected_protocol = None
    for repo, protocol in repositories:
        if protocol is not None:
            selected_repository = repo
            selected_protocol = protocol
            break
    breadcrumbs = paper.breadcrumbs()
    breadcrumbs.append((_('Deposit'), ''))
    context = {
            'paper': paper,
            'max_file_size': DEPOSIT_MAX_FILE_SIZE,
            'available_repositories': repositories,
            'selected_repository': selected_repository,
            'selected_protocol': selected_protocol,
            'is_owner': paper.is_owned_by(request.user),
            'breadcrumbs': breadcrumbs,
            'repositoryForm': None,
            }
    if request.GET.get('type') not in [None, 'preprint', 'postprint', 'pdfversion']:
        return HttpResponseForbidden()
    return render(request, 'deposit/start.html', context)


@user_passes_test(is_authenticated)
def list_deposits(request):
    deposits = DepositRecord.objects.filter(user=request.user,
    identifier__isnull=False).order_by('-date')
    context = {
        'deposits': deposits
    }
    return render(request, 'deposit/deposits.html', context)

@require_POST
@json_view
@user_passes_test(is_authenticated)
def submitDeposit(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    context = {'status': 'error'}
    form = PaperDepositForm(data=request.POST)
    if not form.is_valid():
        context['form'] = form.errors
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
        request_context = RequestContext(request)
        form_html = render_crispy_form(repositoryForm, context=request_context)
        context['form_html'] = form_html
        return context, 400

    # Check that the paper has been uploaded by the same user
    pdf = form.cleaned_data['file_id']
    if pdf.user != request.user:
        context['message'] = _('Access to the PDF was denied.')
        return context, 400

    # Submit the paper to the repository
    path = os.path.join(MEDIA_ROOT, pdf.file.name)

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
        return context, 400

    d.identifier = submitResult.identifier
    d.additional_info = submitResult.additional_info
    d.status = submitResult.status
    d.oairecord = submitResult.oairecord
    d.save()
    paper.update_availability()
    paper.save()
    paper.update_index()

    context['status'] = 'success'
    # TODO change this (we don't need it)
    context['upload_id'] = d.id
    return context
