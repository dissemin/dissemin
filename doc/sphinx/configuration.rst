=============
Configuration
=============

Configure the Application for Development or Production
=======================================================

Finally, create a file ``dissemin/settings/__init__.py`` with this content::

   # Development settings
   from .dev import *
   # Production settings.
   from .prod import *
   # Pick only one.

For most of the settings we refer to the `Django documentation <https://docs.djangoproject.com/en/2.2/topics/settings/>`_.

Logs
====

Dissemin comes with a predefined log system. You can change the settings in ``dissemin/settings/common.py`` and change the default log level for production and development in the corresponding files. When using Dissemin from the shell with ``./manage shell`` you can set the log level for console output as environment variable with::

    export DISSEMIN_LOGLEVEL='YOUR_LOG_LEVEL'

When using in production make sure that apache collects all your log message.
Alternatively you can send them to a separate file by changing log settings.

Sentry
------

Dissemin uses `Sentry <https://sentry.io/welcome/>`_ to monitor severe errors.
To enable Sentry, set the ``SENTRY_DSN``.


ORCID
=====

You can either use production ORCID or its sandbox.
The main difference is the registration process.

*You are not forced to configure ORCID to work on Dissemin, just create a super user and use it!*

.. _configure_orcid_production:

Production
----------

On your ORCID account got to *Developer Tools* and register an API key.
As a redirection URL you give the URL to your installation.

Set ``ORCID_BASE_DOMAIN`` to ``orcid.org`` in the Dissemin settings.

On the admin surface got to *Social Authentication*, set the provider to ``orcid.org`` and enter the required data.

Now you can authenticate with ORCID.

Sandbox
-------

Create an account on `Sandbox ORCID <https://sandbox.orcid.org>`_.

Go to *Developer Tools*, verify your mail using `Mailinator <mailinator.com>`. You must not choose a different provider.

Set up a redirection URI to be `localhost:8080` (supposed to be where your Dissemin instance server is running).

Now proceed as in :ref:`configure_orcid_production`, but with ``sandbox.orcid.org``.
