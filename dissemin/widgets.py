from tempus_dominus.widgets import DatePicker


class OIDatePicker(DatePicker):
    """
    We want to use open iconic instead of font awesome. To not always pass the same options and attributes, we add them in our own widgets
    """

    oi_attrs = {
        'append': 'oi oi-calendar',
    }
    oi_options = {
        'icons' : {
            'clear': 'oi oi-delete',
            'close': 'oi oi-circle-x',
            'date': 'oi oi-calendar',
            'down': 'oi oi-chevron-down',
            'next': 'oi oi-chevron-right',
            'previous': 'oi oi-chevron-left',
            'time': 'oi oi-clock',
            'today': 'oi oi-target',
            'up': 'oi oi-chevron-up',
        },
    }

    def __init__(self, attrs=None, options=None):
        """
        Merges attrs and options into our own definitions
        """

        if isinstance(attrs, dict):
            attrs = {**self.oi_attrs, **attrs}
        else:
            attrs = self.oi_attrs

        if isinstance(options, dict):
            options = {**self.oi_options, **options}
        else:
            options = self.oi_options

        super().__init__(attrs, options)
