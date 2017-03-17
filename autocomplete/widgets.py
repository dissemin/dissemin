from dal.widgets import Select
from dal_select2.widgets import Select2WidgetMixin


class Select2(Select2WidgetMixin, Select):
    """Select2 widget for regular choices."""
