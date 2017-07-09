from dal.widgets import SelectMultiple
from dal_select2.widgets import Select2WidgetMixin


class Select2(Select2WidgetMixin, SelectMultiple):
    """Select2 widget for regular choices."""
