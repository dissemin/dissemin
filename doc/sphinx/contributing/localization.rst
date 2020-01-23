============
Localization
============

We use `Django's standard localization system <https://docs.djangoproject.com/en/2.2/topics/i18n/>`_, based on i18n.
This lets us translate strings in various places.

Localization in Files
=====================

Most localizations are in files:

* in Python code, use ``_("some translatable text")``, where ``_`` is imported by ``from django.utils.translation import ugettext_lazy as _``
* in Javascript code, use ``gettext("some translatable text")``
* in HTML templates, use either ``{% trans "some translatable text" %}`` for inline translations, or, for longer blocks of text::

     {% blocktrans trimmed %}
     My longer translatable text.
     {% endblocktrans %}


  The ``trimmed`` argument is important as it ensures leading and trailing whitespace and newlines are not included in the translation strings (they mess up the translation system).

Localized Models
================

Currently the following models use translations:

* DDC (field ``name``) in ``deposit.models``
* GreenOpenAccessService (fields ``heading, text``) in ``deposit.models``
* License (field ``name``) in ``deposit.models``
* Repository (fields ``name, description``) in ``deposit.models``

For localization we use `django-vinaigrette <https://pypi.org/project/django-vinaigrette/>`_.
Please read their documentation for further information. 
In short: You have to keep in mind that:

* in admin interface you do not see the localized strings,
* you should add only English in the admin interface,
* you will have to recreate the ``*.po`` files and add the translation manually (see below),
* your *local* translations do not interact with TranslateWiki.

From our production environment we have extracted strings from above models.
They are stored in ``model-gettext.py`` so that we have them available for TranslateWiki.

Generating PO files
===================

We have a two way system of generating the PO files.
Most of the translation string can be generated locally, except our strings from the production database (the localized models).
The important thing when generating PO files locally is to preserve the strings from production and do not overwrite them with your local string from your local database.

Vinaigrette saves the strings to be translated in a file called ``vinaigrette-deleteme.py``.
Usually this files is going to be deleted, but we keep it as it carries our translation strings from the models.

Since we use TranslateWiki, we please do not generate any ``.po`` files, as there is a high chance of a merge conflict. Just state that your PR uses localizations, then the Dissemin team will generate to ``.po`` files.

Unless you need localization in your development environment, you can ignore the following sections.


Generate locally
----------------

To generate the PO files, run::

    python manage.py makemessages --keep-pot --no-wrap --no-vinaigrette --ignore doc --ignore .venv

This will generate a PO template `locale/django.pot` that can be used to update the translated files for each language, such as ``locale/fr/LC_MESSAGES/django.po``.
It does not change ``vinaigrette-deleteme.py``.
Note that in some circumstances Django can generate new translation files for languages not yet covered.
In this case these new files should be deleted, as they will break Translatewiki.
It is also necessary to generate separate PO files for JavaScript translations::

   python manage.py makemessages -d djangojs --keep-pot --no-wrap --no-vinaigrette --ignore doc --ignore .venv

You can then compile all the PO files into MO files so that they can be displayed on the website::

    python manage.py compilemessages --exclude qqq

That's it! The translations should show up in your browser if it indicates the target language as your preferred one.
Locale `qqq` contains instructions for translators and therefore does not require compiling (which is worth avoiding since it can contain errors).

Generate from Models
--------------------

On the production environment run::

    python manage.py makemessages --keep-pot --no-wrap --keep-vinaigrette-temp --ignore doc --ignore .venv

This generates locales as above, but generates additionally a ``vinaigrette-deleteme.py``.
Add this file as ``model-gettext.py`` to version control and proceed locally as in above section.

You can safely revert all PO files on production with::

    git checkout -- locale
    git clean -f locale


Available Languages
===================

You can change the set of available languages for your installation in ``dissemin/settings/common.py`` by changing the ``LANGUAGES`` list, e.g. by commenting or uncommenting the corresponding lines.
