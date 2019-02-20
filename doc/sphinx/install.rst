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
- ``vagrant up --provider=your_provider`` will create the VM / container and
  provision the machine once
- ``vagrant ssh`` will let you poke into the machine and access its services
  (PostgreSQL, Redis, ElasticSearch)
- A tmux session is running so that you can check out the Celery and Django
  development server, attach it using: ``tmux attach``. It contains a ``bash``
  panel, two panels to check on Celery and Django development server and a
  panel to create a superuser (admin account) for Dissemin, which you can then
  use from `localhost:8080/admin`.

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
``postgresql postgresql-server-dev-all postgresql-client python3-venv build-essential libxml2-dev libxslt1-dev python3-dev gettext libjpeg-dev libffi-dev``

Then, build a virtual environment to isolate all the python
dependencies::

   python3 -m venv .virtualenv
   source .virtualenv/bin/activate
   pip install --upgrade setuptools
   pip install --upgrade pip
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
backend for Haystack. The current supported version is **2.x.x**.

`Download Elasticsearch <https://www.elastic.co/downloads/elasticsearch>`_
and unzip it::

    cd elasticsearch-<version>
    ./bin/elasticsearch    # Add -d to start elasticsearch in the background

Alternatively you can install the .rpm or .deb package, see the documentation of Elasticsearch for further information.

Make sure to set the initial `heapsize <https://www.elastic.co/guide/en/elasticsearch/reference/2.4/setup-configuration.html#_environment_variables>` accordingly.

Configure the application for development or production
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, create a file ``dissemin/settings/__init__.py`` with this content::

   # Development settings
   from .dev import *
   # Production settings.
   from .prod import *
   # Pick only one.

Depending on your environment, you might want to override ``STATIC_ROOT`` and ``MEDIA_ROOT``, in your ``__init__.py`` file. Moreover, you have to create these locations.

Don't forget to edit ``ALLOWED_HOSTS`` for production or if your django server does not run on *localhost:8080*.

Common settings are available at ``dissemin/settings/common.py``.
Travis specific settings are available at ``dissemin/settings/travis.py``.

Create the database structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is done by applying migrations::

   python manage.py migrate

(this should be done every time the source code is updated).
Then you can move on to :ref:`page-deploying`.

Populate the database with test data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dissemin comes with some sample data for development. You can use djangos *loaddata*::

    django-admin loaddata

Note that this overwrites existing primary keys in your database.

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

In production you want to run ``celery`` and ``celerybeat`` as a daemon and be controlled by ``systemd``. ``celery`` and ``celerybeat`` are installed in the virtual environment of dissemin, so you have to take care, to use this environment. In particular you should use the same user for dissemin and celery.

You can use the following sample files. Put this into ``/etc/default/celery`` and change ``CELERY_BIN`` path.::

    # See
    # http://docs.celeryproject.org/en/latest/tutorials/daemonizing.html#available-options

    CELERY_APP="dissemin.celery:app"
    CELERYD_NODES="dissem"
    CELERYD_OPTS=""
    CELERY_BIN="/path/to/venv/env/bin/celery"
    CELERYD_PID_FILE="/var/run/celery/%n.pid"
    CELERYD_LOG_FILE="/var/log/celery/%n.log"
    CELERYD_LOG_LEVEL="INFO"

    CELERYBEAT_SCHEDULE_FILE="/var/run/celery/beat-schedule"
    CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
    CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"


For ``celeryd`` systemd service put the following in ``/etc/systemd/system/celery.service`` and change ``WorkingDirectory`` to your dissemin root.::

    [Unit]
    Description=Celery Service
    After=network.target

    [Service]
    Type=forking
    User=dissemin
    Group=dissemin
    EnvironmentFile=-/etc/default/celery
    WorkingDirectory=/path/to/dissemin/
    ExecStart=/bin/sh -c '${CELERY_BIN} multi start ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
    ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} --pidfile=${CELERYD_PID_FILE}'
    ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

    [Install]
    WantedBy=multi-user.target

For ``celeryd`` systemd service put the following in ``/etc/systemd/system/celerybeat.service`` and change ``WorkingDirectory`` to your dissemin root.::

    [Unit]
    Description=Celerybeat Service
    After=network.target

    [Service]
    Type=simple
    User=dissemin
    Group=dissemin
    EnvironmentFile=-/etc/default/celery
    WorkingDirectory=/path/to/dissemin/
    ExecStart=/bin/sh -c 'PYTHONPATH=$(pwd) ${CELERY_BIN} beat -A ${CELERY_APP} --pidfile=${CELERYBEAT_PID_FILE} --logfile=${CELERYBEAT_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} -s ${CELERYBEAT_SCHEDULE_FILE}'
    ExecStop=/bin/kill -s TERM $MAINPID

    [Install]
    WantedBy=multi-user.target

To make systemd create the necessary directories with permissions put the follwing into ``/etc/tmpfiles.d/celery.conf``::

    d /var/run/celery 0755 dissemin dissemin
    d /var/log/celery 0755 dissemin dissemin

After that run ``systemctl daemon-reload`` to reload systemd service files and you are ready to use ``celery`` and ``celerybeat`` with systemd.

Importing papers
~~~~~~~~~~~~~~~~

When running a test instance on Dissemin on your local machine, the database
should be preconfigured to contain some papers. However, if you would like to
test different papers, you can easily import more papers in the database of the
test instance by visiting ``localhost:8080/DOI`` where ``DOI`` is the DOI of the
paper that you would like to create.

