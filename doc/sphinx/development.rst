.. _page-development:

Contributing to dissemin
========================

This section explains how to do some development tasks on the source code.

Localization
------------

We use `Django's standard localization system`__, based on i18n.
To generate the PO file, let's say for french, run::

    python manage.py makemessages -l fr

Once you haved filled the translations, compile them so that they can be displayed on the website::

    python manage.py compilemessages

That's it! The translations should show up in your browser if it indicates
the target language as your preferred one.

.. _Django's standard localization system: https://docs.djangoproject.com/en/1.8/topics/i18n/

Writing an interface for a new repository
-----------------------------------------

TODO


