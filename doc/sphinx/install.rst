.. _page-install:

Installation
============

There are two ways to install Dissemin. The automatic way uses
`Vagrant <https://www.vagrantup.com>`_ to install Dissemin to a container or VM,
and only takes a few commands. The manual way is more complex and is
described afterwards.

Automatic installation with `Vagrant <https://www.vagrantup.com>`_
------------------------------------------------------------------

First, install `Vagrant <https://www.vagrantup.com>`_ and one of the supported providers: VirtualBox (should work fine), LXC (tested), libvirt (try it and tell us!). Then run the following commands:

- ``git clone https://github.com/dissemin/dissemin`` will clone the repository,
  i.e., download the source code of Dissemin. You should not reuse an existing
  copy of the repository, otherwise it may cause errors with Vagrant later.
- ``cd dissemin`` to go in the repository
- ``vagrant up --provider=your_provider`` will create the VM / container and provision the machine once
- ``vagrant ssh`` will let you poke into the machine and access its services (PostgreSQL, Redis, ElasticSearch)
- A tmux session is running so that you can check out the Celery and Django development server, attach it using: ``tmux attach``

Dissemin will be available on your host machine at `localhost:8080`.

Note that, when rebooting the Vagrant VM / container, the Dissemin server will
not be started automatically. To do it, once you have booted the machine, run
``vagrant ssh`` and then ``cd /dissemin`` and ``./launch.sh`` and wait for some
time until it says that Dissemin has started. The same holds for other backend
services, you can check the ``Vagrantfile`` and ``provisioning/provision.sh``
to find out how to start them.

Manual installation
-------------------

This section describes manual installation, if you cannot or do not want to use
Vagrant as indicated above. dissem.in is split in two parts:

* the web frontend, powered by Django;
* the tasks backend, powered by Celery.

Installing the tasks backend requires additional dependencies and is not
necessary if you want to do light dev that does not require harvesting
metadata or running author disambiguation. The next subsections describe how to
install the frontend; the last one explains how to install the backend or how to
bypass it in case you do not want to install it.

Installation instructions for the web frontend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install the following dependencies (debian packages)
``postgresql postgresql-server-dev-all postgresql-client python-virtualenv build-essential libxml2-dev libxslt1-dev python-dev gettext libjpeg-dev libffi-dev``

Then, build a virtual environment to isolate all the python
dependencies::

   virtualenv .virtualenv
   source .virtualenv/bin/activate
   pip install --upgrade setuptools
   pip install -r requirements.txt

Set up the database
~~~~~~~~~~~~~~~~~~~

Choose a unique database and user name (they can be identical), such as
``dissemin_myuni``. Choose a strong password for your user::

   sudo su postgres
   psql
   CREATE USER dissemin_myuni WITH PASSWORD 'b3a55787b3adc3913c2129205821765d';
   ALTER USER dissemin_myuni CREATEDB;
   CREATE DATABASE dissemin_myuni WITH OWNER dissemin_myuni;

Configure the secrets
~~~~~~~~~~~~~~~~~~~~~

Copy ``dissemin/settings/secret_template.py`` to ``dissemin/settings/secret.py``.
Edit this file to change the following settings:

- Create a fresh ``SECRET_KEY`` (any random-looking string that you can keep secret will do).

- Configure the ``DATABASES`` with the database you've set up earlier.

- (Optional) Set up the SMTP parameters to send emails to authors, in the ``EMAIL`` section.

- ``ROMEO_API_KEY`` and ``PROAIXY_API_KEY`` are required if you want to
  import papers automatically from these sources.
  See :ref:`page-apikeys` about how to get them.


Install and configure the search engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dissem.in uses the `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_
backend for Haystack.

`Download Elasticsearch <https://www.elastic.co/downloads/elasticsearch>`_
and unzip it::

    cd elasticsearch-<version>
    ./bin/elasticsearch    # Add -d to start elasticsearch in the background

Configure the application for development or production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, create a file ``dissemin/settings/__init__.py`` with this content::

   # Development settings
   from .dev import *
   # Production settings.
   from .prod import *
   # Pick only one.

Depending on your environment, you might want to override ``STATIC_ROOT`` and ``MEDIA_ROOT``, in your ``__init__.py`` file. Moreover, you have to create these locations.

Don't forget to edit ``ALLOWED_HOSTS`` for production.

Common settings are available at ``dissemin/settings/common.py``.
Travis specific settings are available at ``dissemin/settings/travis.py``.

Create the database structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is done by applying migrations::

   python manage.py migrate

(this should be done every time the source code is updated).
Then you can move on to :ref:`page-deploying`.

Populate the search index
~~~~~~~~~~~~~~~~~~~~~~~~~

The search engine must be synchronized with the database manually using::

    python manage.py update_index

That command should be run regularly to index new entries.

Social Authentication specific: Configuring sandbox ORCID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*You are not forced to configure ORCID to work on Dissemin, just create a super user and use it!*

Create an account on `Sandbox ORCID <sandbox.orcid.org>`_.

Go to "Developer Tools", verify your mail using `Mailinator <mailinator.com>`.

Set up a redirection URI to be `localhost:8080` (supposed to be where your Dissemin instance server is running).

Take your client ID and your secret key, you'll use them later.

Ensure that in the settings, you have ``BASE_DOMAIN`` set up to ``sandbox.orcid.org``.

Create a super user::

   python manage.py createsuperuser

Browse to ``localhost:8080/admin`` and log in the administration interface.
Go to "Social Application" and add a new one. Set the provider to ``orcid.org``.

Here, you can use your app ID as your client ID and the secret key that you were given by ORCID earlier.
You should also activate the default Site object for this provider.

Now, you can authenticate yourself using the ORCID sandbox!

Add deposit interfaces
~~~~~~~~~~~~~~~~~~~~~~

If you want to enable deposit of papers to external repositories (such as Zenodo),
you need to register them in the admin interface.

The page `localhost:8080/admin/deposit/repository/` lists the currently registered
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


Installing or bypassing the tasks backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some features in Dissemin rely on an asynchronous tasks backend, celery.
If you want to simplify your installation and ignore this asynchronous
behaviour, you can add ``CELERY_ALWAYS_EAGER = True`` to your
``dissemin/settings/__init__.py``. This way, all asynchronous tasks will
be run from the main thread synchronously.

Otherwise, you need to run celery in a separate process. The rest of this
subsection explains how.

The backend communicates with the frontend through a message passing
infrastructure. We recommend redis for that (and the source code is
configured for it). This serves also as a cache backend (to cache template
fragments) and provides locks (to ensure that we do not fetch the publications
of a given researcher twice, for instance).

First, install the redis server::

   apt-get install redis-server

(this launches the redis server).:

To run the backend (still in the virtualenv)::

   celery --app=dissemin.celery:app worker -B -l INFO

The -B option starts the scheduler for periodic tasks, the -l option sets the debug level
to INFO.


Importing papers
~~~~~~~~~~~~~~~~

When running a test instance on Dissemin on your local machine, the database
should be preconfigured to contain some papers. However, if you would like to
test different papers, you can easily import more papers in the database of the
test instance by visiting ``localhost:8080/DOI`` where ``DOI`` is the DOI of the
paper that you would like to create.

