from django import forms
from django.utils.translation import ugettext_lazy as _
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm
from publishers.models import OA_STATUS_CHOICES_WITHOUT_HELPTEXT as OA_STATUS


class PublisherForm(SearchForm):
    SORT_CHOICES = [
        ('POPULARITY', _('popularity')),
        ('NAME', _('name')),
    ]
    ORDER_CHOICES = [
        (False, _('increasing')),
        (True, _('decreasing')),
    ]
    oa_status = forms.MultipleChoiceField(
        choices=OA_STATUS,
        label=_('Filter by publisher policy'),
        widget=forms.CheckboxSelectMultiple,
        required=False)
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False)
    reverse_order = forms.BooleanField(widget=forms.Select(choices=ORDER_CHOICES), required=False)

    def search(self):
        queryset = super(PublisherForm, self).search()

        if not self.is_valid():
            return EmptyQuerySet()

        if self.cleaned_data['oa_status']:
            queryset = queryset.filter(oa_status__in=self.cleaned_data['oa_status'])

        if self.cleaned_data['sort_by'] == 'NAME':
            queryset = queryset.order_by('name')
        else:
            queryset = queryset.order_by('num_papers')

        if self.cleaned_data['reverse_order']:
            queryset = queryset.reverse()

        return queryset

    def no_query_found(self):
        return SearchQuerySet()
