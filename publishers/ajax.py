'''
Created on 21 févr. 2019

@author: antonin
'''

from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_POST
from papers.user import is_admin
from publishers.models import OA_STATUS_CHOICES
from publishers.models import Publisher
from publishers.tasks import change_publisher_oa_status

@user_passes_test(is_admin)
@require_POST
def change_publisher_status(request):
    allowedStatuses = [s[0] for s in OA_STATUS_CHOICES]
    try:
        pk = request.POST.get('pk')
        publisher = Publisher.objects.get(pk=pk)
        status = request.POST.get('status')
        if status in allowedStatuses and status != publisher.oa_status:
 
            change_publisher_oa_status.delay(pk=pk, status=status)
            return HttpResponse('OK', content_type='text/plain')
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        return HttpResponseNotFound('NOK', content_type='text/plain')
    
urlpatterns = [
    url(r'^change-publisher-status$', change_publisher_status,
        name='ajax-changePublisherStatus'),
]
