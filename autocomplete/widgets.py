from django import forms
from django.conf import settings # NOQA
from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
from django.utils.translation import get_language
from django_select2.forms import HeavySelect2Widget


class Select2(HeavySelect2Widget):
    """
    Select2 widget for regular choices.
    """
    @property
    def media(self):
        """
        Construct Media as a dynamic property.
        .. Note:: For more information visit
            https://docs.djangoproject.com/en/stable/topics/forms/media/#media-as-a-dynamic-property
        """
        lang = get_language()
        select2_js = (settings.SELECT2_JS,) if settings.SELECT2_JS else ()
        select2_css = (settings.SELECT2_CSS,) if settings.SELECT2_CSS else ()

        i18n_name = SELECT2_TRANSLATIONS.get(lang)
        if i18n_name not in settings.SELECT2_I18N_AVAILABLE_LANGUAGES:
            i18n_name = None

        i18n_file = (
            ('%s/%s.js' % (settings.SELECT2_I18N_PATH, i18n_name),)
            if i18n_name
            else ()
        )

        return forms.Media(
            js=select2_js + i18n_file + ('libs/django_select2.js',),
            css={'screen': select2_css}
        )
