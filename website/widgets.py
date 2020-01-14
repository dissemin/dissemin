from tempus_dominus.widgets import DatePicker


class OIDatePicker(DatePicker):
    """
    We want to use open iconic instead of font awesome. To not always pass the same options and attributes, we add them in our own widgets
    """

    oi_attrs = {
        'append': 'oi oi-calendar',
    }
    oi_options = {
        'buttons' : {
            'showClear' : True,
            'showClose' : True,
        },
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
        'useCurrent' : False,
    }

    def __init__(self, attrs={}, options={}):
        """
        Merges attrs and options into our own definitions
        """

        attrs = {**self.oi_attrs, **attrs}

        options = {**self.oi_options, **options}

        super().__init__(attrs, options)
