from django import forms

from deposit.forms import BaseMetadataForm

class SWORDMETSForm(BaseMetadataForm):
    """
    Form that extends BaseMetadataForm for extra fields needed by SWORDMETS
    """

    field_order = ['email', 'abstract', 'ddc', 'license']

    email = forms.EmailField(
        required=True,
        max_length=255,
    )
