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

from dissemin.settings import MEDIA_ROOT, UNIVERSITY_BRANDING, DEPOSIT_MAX_FILE_SIZE 

from deposit.models import *
from deposit.forms import *
from sword.submitOnZenodo import *
from papers.models import Paper
from papers.user import is_admin, is_authenticated

@user_passes_test(is_authenticated)
def start_view(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    context = {'paper':paper, 'max_file_size':DEPOSIT_MAX_FILE_SIZE}
    if request.GET.get('type') not in [None,'preprint','postprint','pdfversion']:
        return HttpResponseForbidden()
    return render(request, 'deposit/start.html', context)

@user_passes_test(is_authenticated)
def submitDeposit(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    if request.method == 'POST':
        context = {'status':'error'}
        form = PaperDepositForm(request.POST)

        if not form.is_valid():
            context['form'] = form.errors
            return HttpResponseForbidden(json.dumps(context), content_type='text/json')

        # Check that the paper has been uploaded by the same user
        pdf = form.cleaned_data['file_id']
        if pdf.user_id != request.user.id:
            context['message'] = _('Access to the PDF was denied.')
            return HttpResponseForbidden(json.dumps(context))

        # Create initial record
        d = DepositRecord(
                paper=paper,
                user=pdf.user,
                upload_type=form.cleaned_data['radioUploadType'],
                file=pdf)
        d.save()

        # Submit paper to Zenodo
        path = os.path.join(MEDIA_ROOT, pdf.file.name)
        
        zenodo = {}
        try:
            zenodo = submitPubli(paper, path)
        except DepositError as e:
            d.request = e.logs+'\nMessage: '+str(e)
            d.save()
            context['message'] = str(e)
            return HttpResponseForbidden(json.dumps(context), content_type='text/json')

        d.identifier = zenodo.get('identifier')
        d.pdf_url = zenodo.get('pdf_url')
        d.request = zenodo.get('logs')
        d.save()

        context['status'] = 'success'
        context['upload_id'] = d.id
        return HttpResponse(json.dumps(context), content_type='text/json')
    return HttpResponseForbidden()


