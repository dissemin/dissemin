from django import forms

from django.utils.translation import ugettext_lazy as _

from deposit.forms import BaseMetadataForm

class SWORDMETSForm(BaseMetadataForm):
    """
    Form that extends BaseMetadataForm for extra fields needed by SWORDMETS
    """

    field_order = ['email', 'abstract', 'ddc', 'license']

    email = forms.EmailField(
        label=_('E-mail'),
        required=True,
        max_length=255,
    )
