from django import forms
from django.utils.translation import ugettext_lazy as _
from haystack.forms import SearchForm
from publishers.models import OA_STATUS_CHOICES_WITHOUT_HELPTEXT as OA_STATUS
from publishers.models import Publisher


class PublisherForm(SearchForm):
    SORT_CHOICES = [
        ('num_papers', _('popularity')),
        ('name', _('name')),
    ]
    ORDER_CHOICES = [
        ('dec', _('decreasing')),
        ('inc', _('increasing')),
    ]
    q = forms.CharField(
        label=_("By publisher"),
        required=False,
    )
    oa_status = forms.MultipleChoiceField(
        choices=OA_STATUS,
        label=_('By publisher policy'),
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'form-check-input'}
            ),
        required=False
        )
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        label=_("Sort by"),
        required=False,
        widget=forms.Select(
            attrs={'class': 'custom-select'}),
    )
    reverse_order = forms.ChoiceField(
        choices=ORDER_CHOICES,
        label=_("Order"),
        required=False,
        widget=forms.Select(
            attrs={'class': 'custom-select'}),
    )

    def search(self):
        queryset = self.searchqueryset.models(Publisher).load_all()

        q = self.cleaned_data['q']
        if q:
            queryset = queryset.auto_query(q)

        if self.cleaned_data['oa_status']:
            queryset = queryset.filter(
                oa_status__in=self.cleaned_data['oa_status'])

        # Default ordering by decreasing popularity
        order = self.cleaned_data['sort_by'] or 'num_papers'
        reverse_order = self.cleaned_data['reverse_order'] != 'inc'
        if reverse_order:
            order = '-' + order

        queryset = queryset.order_by(order)

        return queryset
