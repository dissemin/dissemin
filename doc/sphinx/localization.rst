.. _page-localization:

Localization
------------

Translations are hosted at `TranslateWiki
<https://translatewiki.net/wiki/Translating:Dissemin>`_, for an easy-to-use
interface for translations and statistics.

We use `Django's standard localization system <https://docs.djangoproject.com/en/1.8/topics/i18n/>`_, based on i18n.
To generate the PO file, let's say for french, run::

    python manage.py makemessages -l fr

Once you haved filled the translations in ``locale/fr/LC_MESSAGES/django.po``,
compile them so that they can be displayed on the website::

    python manage.py compilemessages

That's it! The translations should show up in your browser if it indicates
the target language as your preferred one.


