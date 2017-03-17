"""
At the moment, this module will load API urls only if restframework is available.
"""

from django.conf import settings

if 'rest_framework' in settings.INSTALLED_APPS:
    from rest_framework.routers import DefaultRouter
    from django.conf.urls import url, include
    from . import views

    router = DefaultRouter()
    router.register(r'inbox', views.InboxViewSet, base_name='inbox')

    urlpatterns = [
        url(r'^', include(router.urls))
    ]
else:
    urlpatterns = []
