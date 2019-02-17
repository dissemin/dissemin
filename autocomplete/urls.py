# -*- encoding: utf-8 -*-


from autocomplete import views
from django.conf.urls import url

urlpatterns = [
    url(r'^autocomplete_affiliations/$',
        views.AffiliationAutocomplete.as_view(),
        name='autocomplete_affiliations')
]
