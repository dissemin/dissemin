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


Shibboleth
==========

Shibboleth is a SAML based authentication mechanism and widely used in academic research.
CAPSH has joined the French federation `RENATER <https://www.renater.fr/>`__ in order to provide a login with eduGAIN.
In the SAML world there is usually an IdentityProvider (IdP) that permits (local) authentication and a Service Provider (SP) that offers some kind of service. In this case, https://dissem.in/ will be the SP.

Relevant documentations can be found at `Shibboleth <https://wiki.shibboleth.net/confluence/display/SP3/Home>`__ and `RENATER <https://services.renater.fr/federation/en/documentation/index>`__. They cover some of the understanding of how Shibboleth works as well as instructions on participating and register a SP.

The ``entityID`` for our production service is ``https://sp.dissem.in/shibboleth`` while we use ``https://sp.sandbox.dissem.in/shibboleth`` for our sandbox.
The guide assumes in the following, that production and sandbox run on the same machine.


Installation
------------

Shibboleth requires ``mod_shibboleth`` and a daemon.
Official packages are available for RedHat and openSUSE.
For Ubuntu and Debian based system, please follow the `guide from SWITCHaai <https://www.switch.ch/aai/guides/sp/installation/>`_.

The certs and keys for signing and encryption might be missing.
They can be self signed certificates.
To generate them, run::

    openssl req -config config-cert.conf -new -x509 -nodes -days 1095 -keyout sp-encrypt-key.pem -out sp-encrypt-cert.pem
    openssl req -config config-cert.conf -new -x509 -nodes -days 1095 -keyout sp-signing-key.pem -out sp-signing-cert.pem

where the config file looks like::

    [ req ]
    default_bits = 4096
    distinguished_name = req_distinguished_name
    prompt = no
    x509_extensions = req_ext

    [ req_distinguished_name ]
    C = FR
    O = CAPSH
    CN = dissem.in
    emailAddress = team@dissem.in

    [req_ext ]
    subjectAltName = @alt_names

    [ alt_names ]
    DNS.1 = dissem.in
    DNS.2 = sandbox.dissem.in
    DNS.3 = https://sp.dissem.in/shibboleth # entityID production
    DNS.4 = https://sp.sandbox.dissem.in/shibboleth # entityID sandbox

.. warning::
    When the certificates expire and we have to renew them, we must communicate to RENATER! For a short period of time we have to provide both certificates, the old and new ones, so that the IdPs can update to the new one and the transition is seamless.

.. note::
    In theory, we can use the same certificate as for the https server, but this is disadvantageous with Let's Encrypt since with every new certificate, we would need to change our shibboleth metadata.


shibboleth2.xml
---------------

This is the central configuration file for Shibboleth where the magic happens.
After a change of the configuration, touch the file, to tell the shibboleth deamon to reload.
This does not disturb the service.
Depending on the changes, the metadata for our entityId change.

Since RENATER offers a production as well a test federation, we need to create different metadata.
This will be done via `ApplicationOverride <https://wiki.shibboleth.net/confluence/display/SP3/ApplicationOverride>`_ as there are little differences only, that must be set explicetely:

* entityID
* discoveryURL
* MetadataProvider
* MetadataGenerator

You can find our (sample) ``shibboleth2.xml`` als well as our ``attribute-map.xml`` in our GitHub repository. Check the folder ``provisioning``.

Make also sure, that the settings comply with `SAML Metadata Published by RENATER <https://services.renater.fr/federation/en/documentation/generale/metadata/index>`_.


Apache
------

In order to make Shibboleth available on the virtual host, add::

    <Location /Shibboleth.sso>
        setHandler shib
    </Location>

This way Shibboleth gets precedence over WSGI for ``/Shibboleth.sso``.
In theory, you could use any other alias, but this is somewhat of a standard.

For our sandbox, make sure to add::

    <Location />
        ShibRequestSetting applicationId sandbox
    </Location>

right before the WSGI-part.
This makes sure to use the ApplicationOverride for sandbox that we mentioned above.

Troubleshooting
---------------

Systemd timeout
```````````````

Under certain circumstances ``shibd`` does take along time to start.
This is due to the fact that we process the whole eduGAIN IdP metadata.
The crucial time killer is the validation of signatures.

Usually this is only an issue when starting shibd for the first time, since cached IdPs won't be validated again.

There are three ways to solve this:

1. Increase timeout on systemd for shibd
2. Stop shibd and initialize it manually
3. Turn off validation.

Of course, *3.* is not an option!

The standard approach to solve this is usually to use MDQ, where IdPs will be checked in case of need.
This system is not (yet) suitable for a DiscoveryService since it needs to know all IdPs.
