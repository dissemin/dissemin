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

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from itertools import groupby

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from deposit.models import Repository
from deposit.models import UserPreferences
from deposit.declaration import REGISTERED_DECLARATION_FUNCTIONS
from deposit.registry import protocol_registry
from dissemin.widgets import OIDatePicker
from papers.models import UPLOAD_TYPE_CHOICES
from upload.models import UploadedPDF


class ModelGroupedMultipleChoiceField(forms.models.ModelMultipleChoiceField):
    """
    Enabled groups for ModelMultipleChoiceField
    """
    def __init__(self, group_by_field, group_label=None, *args, **kwargs):
        """
        :param group_by_field: name of a field on the model to use for grouping
        :param group_label: function to return a label for each choice group
        """
        super().__init__(*args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return ModelGroupedChoiceIterator(self)

    choices = property(_get_choices, forms.models.ModelMultipleChoiceField._set_choices)


class ModelGroupedChoiceIterator(forms.models.ModelChoiceIterator):
    """
    Iterator for ModelGroupedChoiceField
    """
    def __iter__(self):
        if self.field.empty_label is not None:
            yield self.field.empty_label
        for group, choices in groupby(
                self.queryset.all(),
                key=lambda row: getattr(
                    row, self.field.group_by_field)):
            if group is not None:
                yield (self.field.group_label(group), [self.choice(ch) for ch in choices])


class PaperDepositForm(forms.Form):
    """
    Main form for the deposit.
    It references both the file (as an ID) and the upload type.
    """
    file_id = forms.IntegerField()
    radioUploadType = forms.ChoiceField(
        choices=UPLOAD_TYPE_CHOICES,
        label=_('Upload type'),
        widget=forms.RadioSelect,
    )
    radioRepository = forms.ModelChoiceField(label=_('Repository'),
                                             queryset=Repository.objects.filter(enabled=True))

    def clean_file_id(self):
        file_id = self.cleaned_data['file_id']
        try:
            uploadedPDF = UploadedPDF.objects.get(pk=file_id)
        except UploadedPDF.NotFound:
            raise forms.ValidationError(
                _("Invalid full text identifier."), code='invalid_file_id')
        return uploadedPDF


def wrap_with_prefetch_status(baseWidget, callback, fieldname):
    """
    Add a status text above the widget to display the prefetching status
    of the data in the field.

    :param baseWidget: the :class:`Widget` to be prefetched: the prefetching
            status will be displayed above that widget and its value will
            be set by the JS code
    :param get_callback: function returning the AJAX URL where to get
        the prefetching status from. This is a callback and not a plain
        string for technical reasons (the URL cannot be computed before
        Django is fully loaded).
    :param fieldname: The name of the field to be prefetched, passed
        to the AJAX callback.
    """
    orig_render = baseWidget.render

    def new_render(self, name, value, attrs=None, renderer=None):
        base_html = orig_render(self, name, value, attrs, renderer)
        if value:
            return base_html
        return ('<span class="prefetchingFieldStatus" data-callback="%s" data-fieldid="%s" data-fieldname="%s" data-objfieldname="%s"></span>' % (callback, attrs['id'], name, fieldname))+base_html
    baseWidget.render = new_render
    return baseWidget


class BaseMetadataForm(forms.Form):
    """
    Base form for repository-specific options and metadata. Protocols can subclass this form and add or remove fields.
    """

    field_order = ['abstract', 'ddc', 'license']

    # Dummy field to store the paper id (required for dynamic fetching of the abstract)
    paper_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput
    )
    # Abstract field to
    abstract = forms.CharField(
            label=_('Abstract'),
            widget=wrap_with_prefetch_status(
                forms.Textarea,
                reverse_lazy('ajax-waitForConsolidatedField'),
                'paper_id')(attrs={'class': 'form-control'})
            )
    
    # DDC field to choose DDC classes
    ddc = ModelGroupedMultipleChoiceField(
        label=_('Dewey Decimal Class'),
        queryset=None,
        group_by_field='parent',
        widget=forms.SelectMultiple
    )

    embargo = forms.DateField(
        label=_('Do not publish before'),
        widget=OIDatePicker(),
    )

    # License field to choose license
    license = forms.ModelChoiceField(
        label=_('License'),
        queryset=None,
        empty_label=None,
        initial=None,
        widget=forms.RadioSelect,
    )

    def __init__(self, **kwargs):
        """
        Subclasses can reimplement this and do things based on the models passed or generally add or remove fields.
        The paper_id field is not filled here, because that should only happen when filling the form with initial data.
        """
        abstract_required = kwargs.pop('abstract_required', True)
        ddcs = kwargs.pop('ddcs', None)
        embargo = kwargs.pop('embargo', None)
        licenses = kwargs.pop('licenses', None)

        super(BaseMetadataForm, self).__init__(**kwargs)

        # Mark abstract as required or not
        self.fields['abstract'].required = abstract_required
        
        # If no DDC for repository choosen, then delete field from form
        if ddcs is None:
            del(self.fields['ddc'])
        else:
            self.fields['ddc'].queryset = ddcs

        # Handle embargo field
        if embargo == 'required':
            self.fields['embargo'].required = True
        elif embargo == 'optional':
            self.fields['embargo'].required = False
        else:
            del(self.fields['embargo'])


        # If no licenses for repository choosen, then delete field from form
        if licenses is None:
            del(self.fields['license'])
        else:
            self.fields['license'].queryset = licenses


### Form for global preferences ###

class PreferredRepositoryField(forms.ModelChoiceField):
    queryset = Repository.objects.filter(enabled=True)
    def __init__(self, *args, **kwargs):
        kwargs['empty_label'] = _('No preferred repository')
        kwargs['queryset'] = Repository.objects.filter(enabled=True)
        super(PreferredRepositoryField, self).__init__(*args, **kwargs)

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['email', 'preferred_repository']
        widgets = {
            'preferred_repository': forms.RadioSelect(attrs={'class':'radio-margin'}),
        }
        field_classes = {
            'preferred_repository': PreferredRepositoryField,
        }

    def __init__(self, *args, **kwargs):
        super(UserPreferencesForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        #self.helper.form_class = 'form-horizontal'
        #self.helper.label_class = 'col-lg-2'
        #self.helper.field_class = 'col-lg-8'
        self.helper.add_input(
            Submit('submit', _('Save')),
        )

class RepositoryAdminForm(forms.ModelForm):
    """
    We change here to widgets for chosing the Protocol and the Declaration.
    Instead of free text we provide a dropdown.
    """
    
    def __init__(self, *args, **kwargs):
        """
        We change the widget of the fields
        We get the original form, register all repositories, create the list of protocols.
        If a repo exists, we check that its protocol will be in the list. Otherwise the protocol of a repo with a currently not registered protocol would be overwritten.
        """
        super().__init__(*args, **kwargs)

        # Protocol
        # Get the list with names of protocols
        protocol_registry.load()
        choices = [(key, str(value)) for key, value in protocol_registry.dct.items()]
        # If the repo uses a protocol not in the list, we add this value, otherwise it is overriden on saving
        if self.instance.protocol:
            if self.instance.protocol not in protocol_registry.dct.keys():
                choices += [(self.instance.protocol,self.instance.protocol)]
        # Sort and populate the form
        choices = sorted(choices, key=lambda protocol: protocol[1].lower(),)
        self.fields['protocol'].widget = forms.Select(choices=choices)

        # Letter of Declaration
        # Get the list of user friendly names of the generating functions. We need them as tuple for djangos choices
        choices = [(value, value) for value in REGISTERED_DECLARATION_FUNCTIONS]
        choices = [('', None)] + sorted(choices, key=lambda item: item[1])
        self.fields['letter_declaration'].widget = forms.Select(choices=choices)
