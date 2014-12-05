# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from papers.models import *

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def deletePaper(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    paper.visibility = 'DELETED'
    paper.save(update_fields=['visibility'])
    return HttpResponse('OK', mimetype='text/plain')


