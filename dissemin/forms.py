from django.utils.translation import ugettext as _

from papers.forms import PaperForm


class StartPageSearchForm(PaperForm):
    """
    Simple form for the start page to start searching
    """
    def __init__(self, *args, **kwargs):
        """
        Here we adjust title and placeholder of the form
        """
        super().__init__(*args, **kwargs)
        self.fields['authors'].widget.attrs.update({
            'placeholder': _('Try any author name')
        })
        self.fields['authors'].widget.attrs.update({
            'title': _('Try any author name')
        })
