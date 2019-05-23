.. _page-localization:

Localization
------------

Translations are hosted at `TranslateWiki
<https://translatewiki.net/wiki/Translating:Dissemin>`_, for an easy-to-use
interface for translations and statistics.

We use `Django's standard localization system <https://docs.djangoproject.com/en/2.2/topics/i18n/>`_, based on i18n.
This lets us translate strings in various places:

* in Python code, use ``_("some translatable text")``, where ``_`` is imported by ``from django.utils.translation import ugettext_lazy as _``
* in Javascript code, use ``gettext("some translatable text")``
* in HTML templates, use either ``{% trans "some translatable text" %}`` for inline translations, or, for longer blocks of text::

     {% blocktrans trimmed %}
     My longer translatable text.
     {% endblocktrans %}


  The ``trimmed`` argument is important as it ensures leading and trailing whitespace and newlines are not included in the translation strings (they mess up the translation system).

Localized Models
~~~~~~~~~~~~~~~~

Currently the following models use translations:

* License (field ``name``) in ``deposit.models``

For localization we use `django-vinaigrette <https://pypi.org/project/django-vinaigrette/>`_. Please read their documentation for further information. In short: You have to keep in mind that:

* in admin interface you do not see the localized strings,
* you should add only english in the admin interface,
* you will have to recreate the ``*.po`` files and add the translation manually (see below),
* your local translations do not interact with TranslateWiki.

Generating PO files
~~~~~~~~~~~~~~~~~~~

To generate the PO files, run::

    python manage.py makemessages --keep-pot --ignore doc

This will generate a PO template `locale/django.pot` that can be used to update the translated files for each language,
such as ``locale/fr/LC_MESSAGES/django.po``. Note that in some circumstances Django can generate new translation files
for languages not yet covered. In this case these new files should be deleted, as they will break Translatewiki.
It is also necessary to generate separate PO files for JavaScript translations::

   python manage.py makemessages -d djangojs --keep-pot --ignore doc

You can then compile all the PO files into MO files so that they can be displayed on the website::

    python manage.py compilemessages

That's it! The translations should show up in your browser if it indicates
the target language as your preferred one.

Available Languages
-------------------

You can change the set of available languages for your installation in ``dissemin/settings/common.py`` by changing the ``LANGUAGES`` list, e.g. by commenting or uncommenting the corresponding lines.

