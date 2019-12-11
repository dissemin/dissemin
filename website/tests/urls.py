from django.urls import include
from django.urls import path
from django.views.generic.base import TemplateView

urlpatterns = [
    path('', include('website.urls')),
    path('error/', TemplateView.as_view(template_name='dissemin/error.html'), name='error'),
]
