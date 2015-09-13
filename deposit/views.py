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

import os, json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils.translation import ugettext as _

from dissemin.settings import MEDIA_ROOT, UNIVERSITY_BRANDING, DEPOSIT_MAX_FILE_SIZE 

from deposit.models import *
from deposit.forms import *
from papers.models import Paper
from papers.user import is_admin, is_authenticated

def get_all_protocols(paper, user):
    repositories = Repository.objects.all()
    protocols = []
    for r in repositories:
        implem = r.protocol_for_deposit(paper, user)
        if implem is not None:
            protocols.append(implem)
    return protocols

@user_passes_test(is_authenticated)
def start_view(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    forms = map(lambda i: i.get_form(), get_all_protocols(paper, request.user))
    breadcrumbs = paper.breadcrumbs()
    breadcrumbs.append((_('Deposit'),''))
    context = {
            'paper':paper,
            'max_file_size':DEPOSIT_MAX_FILE_SIZE,
            'forms': forms,
            'is_owner':paper.is_owned_by(request.user),
            'breadcrumbs':breadcrumbs,
            }
    if request.GET.get('type') not in [None,'preprint','postprint','pdfversion']:
        return HttpResponseForbidden()
    return render(request, 'deposit/start.html', context)

@user_passes_test(is_authenticated)
def submitDeposit(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    if request.method != 'POST':
        return HttpResponseForbidden()
    context = {'status':'error'}
    form = PaperDepositForm(request.POST)
    if not form.is_valid():
        context['form'] = form.errors
        return HttpResponseForbidden(json.dumps(context), content_type='text/json')

    protocols = get_all_protocols(paper, request.user)

    repositoryForms = map(lambda i: i.get_bound_form(request.POST), protocols)
    for idx, f in enumerate(repositoryForms):
        if not f.is_valid():
            repositoryForms[idx] = f.errors()
            return HttpResponseForbidden(json.dumps(context), content_type='text/json')

    # Check that the paper has been uploaded by the same user
    pdf = form.cleaned_data['file_id']
    if pdf.user != request.user:
        context['message'] = _('Access to the PDF was denied.')
        return HttpResponseForbidden(json.dumps(context))

    # Submit paper to all repositories (TODO: only a selection)
    path = os.path.join(MEDIA_ROOT, pdf.file.name)

    # TODO delete this
    last_deposit = None
    for idx, p in enumerate(protocols):
        print "Create initial record"
        # Create initial record
        d = DepositRecord(
                paper=paper,
                user=pdf.user,
                repository=p.repository,
                upload_type=form.cleaned_data['radioUploadType'],
                file=pdf)
        d.save()
        last_deposit = d

        submitResult = p.submit_deposit_wrapper(path, repositoryForms[idx])
        
        d.request = submitResult.logs
        if not submitResult.success():
            # TODO error handling when some deposits were successful and
            # some others were not.
            context['message'] = submitResult.message
            d.save()
            return HttpResponseForbidden(json.dumps(context), content_type='text/json')
        print "Deposit succeeded."
        d.identifier = submitResult.identifier
        d.pdf_url = submitResult.pdf_url
        d.save()

    context['status'] = 'success'
    # TODO change this (we don't need it)
    context['upload_id'] = last_deposit.id
    return HttpResponse(json.dumps(context), content_type='text/json')


