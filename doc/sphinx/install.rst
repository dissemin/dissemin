.. _page-install:

Installation
============

dissem.in is split in two parts:

* the web frontend, powered by Django;
* the tasks backend, powered by Celery.

Installing the tasks backend requires additional dependencies and is not
necessary if you want to do light dev that does not require harvesting
metadata or running author disambiguation.

Installation instructions for the web frontend
----------------------------------------------

First, install the following dependencies (debian packages)
``postgresql postgresql-server-dev-all postgresql-client python-virtualenv build-essential libxml2-dev libxslt1-dev python-dev gettext libjpeg-dev``

Then, build a virtual environment to isolate all the python
dependencies::

   virtualenv .virtualenv
   source .virtualenv/bin/activate
   pip install -r requirements_frontend.txt

Set up the database
-------------------

Choose a unique database and user name (they can be identical), such as
``dissemin_myuni``. Choose a strong password for your user::

   sudo su postgres
   psql
   CREATE USER dissemin_myuni WITH PASSWORD 'b3a55787b3adc3913c2129205821765d';
   ALTER USER dissemin_myuni CREATEDB;
   CREATE DATABASE dissemin_myuni WITH OWNER dissemin_myuni;

Configure the secrets
----------------------

Copy ``dissemin/settings/secret_template.py`` to ``dissemin/settings/secret.py``.
Edit this file to change the following settings:

- Create a fresh ``SECRET_KEY`` (any random-looking string that you can keep secret will do).

- Configure the ``DATABASES`` with the database you've set up earlier.

- (Optional) Set up the SMTP parameters to send emails to authors, in the ``EMAIL`` section.

- ``ROMEO_API_KEYS`` is required if you want to
  import papers automatically from these sources. See :ref:`page-apikeys`
  about how to get them. The ``ZENODO_KEY`` is required
  if you want to upload papers to Zenodo.


Configure the university-specific settings
-----------------------------------------

Copy ``dissemin/settings/university_template.py`` to ``dissemin/settings/university.py``.
Then, edit this file to change the following settings:

- Set up the university branding, defining:
    - ``UNIVERSITY_FULL_NAME``: the complete name of the university;
    - ``UNIVERSITY_SHORT_NAME``: the short name (with determiner);
    - ``UNIVERSITY_REPOSITORY_URL``: the address of your university's
      institutional repository, if it has one. This is not intended to
      be the url of an API, simply the address where to redirect users
      to when they want to see the repository;
    - ``UNIVERSITY_URL``: the website of your university.

- Set up the CAS of your university if relevant, it is disabled by default (see  ``ENABLE_CAS``).

Now, your university settings are done.

Install and configure the search engine
---------------------------------------

You can choose any of the search backends supported by Haystack.

Whoosh is the simplest option, as it is written in Python and you can install it via PyPI::

    pip install whoosh

and finally just copy ``dissemin/settings/search_engine_template.py`` to
``dissemin/settings/search_engine.py``.

Configure the application for development or production
-------------------------------------------------------

Finally, create a file ``dissemin/settings/__init__.py`` with this content::

   # Development settings
   from .dev import *
   # Production settings.
   from .prod import *
   # Pick only one.

Depending on your environment, you might want to edit ``STATIC_ROOT`` and ``MEDIA_ROOT``, moreover, you have to create these locations.

Don't forget to edit ``ALLOWED_HOSTS`` for production.

Common settings are available at ``dissemin/settings/common.py``.
Travis specific settings are available at ``dissemin/settings/travis.py``.

Create the database structure
-----------------------------

This is done by applying migrations::

   python manage.py migrate

(this should be done every time the source code is updated).
Then you can move on to :ref:`page-importresearchers`
and :ref:`page-deploying`.

Populate the search index
-------------------------

The search engine must be synchronized with the database manually using::

    python manage.py update_index

That command should be run regularly to index new entries.

Social Authentication specific: Configuring sandbox ORCID
---------------------------------------------------------

*You are not forced to configure ORCID to work on Dissemin, just create a super user and use it!*

Create an account on `Sandbox ORCID <sandbox.orcid.org>`

Go to "Developer Tools", verify your mail using `Mailinator <mailinator.com>`.

Set up a redirection URI to be `localhost:8000` (supposed to be where your Dissemin instance server is running).

Take your client ID and your secret key, you'll use them later.

Ensure that in the settings, you have ``BASE_DOMAIN`` set up to ``sandbox.orcid.org``.

Create a super user::

   python manage.py createsuperuser

Browse to ``localhost:8000/admin`` and log in the administration interface.
Go to "Social Application" and add a new one. Set the provider to ``orcid.org``.

Here, you can use your app ID as your client ID and the secret key that you were given by ORCID earlier.
You should also activate the default Site object for this provider.

Now, you can authenticate yourself using the ORCID sandbox!

Add deposit interfaces
----------------------

If you want to enable deposit of papers to external repositories (such as Zenodo),
you need to register them in the admin interface.

The page `localhost:8000/admin/deposit/repository/` lists the currently registered
interfaces and allows you to add one.

To add a repository, you need the following settings:
- A name, description and logo. They will be shown to the user on the deposit page.
- A protocol: this is the internal name of the protocol Dissemin should use
  to perform the deposit. For now, only `ZenodoProtocol` is available: it can
  be used to deposit to Zenodo (both production and sandbox).
- Some other settings, such as the endpoint of the deposit interface,
  depending on what the protocol you have chosen requires.
  In the case of Zenodo, you need the endpoint (such as `https://zenodo.org/api/deposit/depositions` or `https://sandbox.zenodo.org/api/deposit/depositions`) and the API
  key (available from your account on Zenodo).

A checkbox allows you to enable or disable the repository without deleting its settings.


Optional: installing the tasks backend
--------------------------------------

This part is only required if you want to fetch papers from metadata sources.
This functionality is located in the `backend` module and has separate
dependencies.

The backend communicates with the frontend through a message passing
infrastructure. We recommend redis for that (and the source code is
configured for it). This serves also as a cache backend (to cache template
fragments) and provides locks (to ensure that we do not fetch the publications
of a given researcher twice, for instance).

First, install the redis server::

   apt-get install redis-server

(this launches the redis server). Install Python dependencies::

   sudo apt-get install libxml2 python-dev libxslt-dev liblapack-dev gfortran libopenblas-dev
   source .virtualend/bin/activate
   pip install -r requirements_backend.txt

Optional python dependencies (if you want to debug the learning system)::

   pip install nltk
   pip install matplotlib

To run the backend (still in the virtualenv)::

   celery --app=dissemin.celery:app worker -B -l INFO

The -B option starts the scheduler for periodic tasks, the -l option sets the debug level
to INFO.


