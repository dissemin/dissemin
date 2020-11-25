===================
Manual Installation
===================

This section describes manual installation, if you cannot or do not want to use Vagrant as indicated above.
It also serves as installation guide for production.
Dissemin is split in two parts:


* the web frontend, powered by Django;
* the tasks backend, powered by Celery.

Installing the tasks backend requires additional dependencies and is not necessary if you want to do light dev that does not require harvesting metadata or running author disambiguation.
The next subsections describe how to install the frontend; the last one explains how to install the backend or how to bypass it in case you do not want to install it.

Frontend
========

Install Packages and Create Virtualenv
--------------------------------------

First, install the following dependencies (debian packages)::
    
    *postgresql postgresql-server-dev-all postgresql-client python3-venv build-essential libxml2-dev libxslt1-dev python3-dev gettext libjpeg-dev libffi-dev libmagickwand-dev gdal-bin*

.. note::
    On Debian 10+ and Ubuntu 18+, libmagickwand has dropped PDF processing for security reason. To reenable you have to change the config to at least read access, e.g. with::

        sudo sed -i 's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read" pattern="PDF" \/>/' /etc/ImageMagick-6/policy.xml

Make also sure to have ``pdftk`` installed.

Then, build a virtual environment to isolate all the python dependencies::

   python3 -m venv .virtualenv
   source .virtualenv/bin/activate
   pip install --upgrade setuptools
   pip install --upgrade pip
   pip install -r requirements.txt

In case you want to use the development packages, run addiotionally::

    pip install -r requirements-dev.txt


Database
--------

Choose a unique database and user name (they can be identical), such as ``dissemin_myuni``.
Choose a strong password for your user::

   sudo su postgres
   psql
   CREATE USER dissemin_myuni WITH PASSWORD 'b3a55787b3adc3913c2129205821765d';
   ALTER USER dissemin_myuni CREATEDB;
   CREATE DATABASE dissemin_myuni WITH OWNER dissemin_myuni;


Search Engine
-------------

Dissemin uses the `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_ backend for Haystack. The current supported version is **2.x.x**.

`Download Elasticsearch <https://www.elastic.co/downloads/elasticsearch>`_ and unzip it::

    cd elasticsearch-<version>
    ./bin/elasticsearch    # Add -d to start elasticsearch in the background

Alternatively you can install the .rpm or .deb package, see the documentation of Elasticsearch for further information.

Make sure to set the initial `heapsize <https://www.elastic.co/guide/en/elasticsearch/reference/2.4/setup-configuration.html#_environment_variables>`_ accordingly.

Backend
=======

Some features in Dissemin rely on an asynchronous tasks backend, celery.
If you want to simplify your installation and ignore this asynchronous behaviour, you can add ``CELERY_ALWAYS_EAGER = True`` to your ``dissemin/settings/__init__.py``.
This way, all asynchronous tasks will be run from the main thread synchronously.

Otherwise, you need to run celery in a separate process.
The rest of this subsection explains how.

Redis
-----

The backend communicates with the frontend through a message passing infrastructure.
We recommend redis for that (and the source code is configured for it).
This serves also as a cache backend (to cache template fragments) and provides locks (to ensure that we do not fetch the publications of a given researcher twice, for instance).

First, install the redis server::

   apt-get install redis-server

Celery
------

You can run Celery either in the shell or as daemon.
The letter is recommend for production.

Shell
~~~~~
To run the backend (still in the virtualenv)::

   celery --app=dissemin.celery:app worker -B -l INFO

The -B option starts the scheduler for periodic tasks, the -l option sets the debug level to INFO.

Daemon
~~~~~~

In production you want to run ``celery`` and ``celerybeat`` as a daemon and be controlled by ``systemd``. ``celery`` and ``celerybeat`` are installed in the virtual environment of dissemin, so you have to take care to use this environment.
In particular you should use the same user for Dissemin and Celery.

You should use the following sample files that are similar to the `official sample files <https://github.com/celery/celery/tree/master/extra/systemd>`_. The main differences are a different ``PYTHONPATH``, respect of the virtual environment and ``stop`` command for celerybeat. Put this into ``/etc/default/celery`` and change ``CELERY_BIN`` path.::

    # See
    # http://docs.celeryproject.org/en/latest/userguide/daemonizing.html

    CELERY_APP="dissemin.celery:app"
    CELERYD_NODES="dissem"
    CELERYD_OPTS=""
    CELERY_BIN="/path/to/venv/bin/celery"
    CELERYD_PID_FILE="/var/run/celery/%n.pid"
    CELERYD_LOG_FILE="/var/log/celery/%n.log"
    CELERYD_LOG_LEVEL="INFO"

    CELERYBEAT_SCHEDULE_FILE="/var/run/celery/beat-schedule"
    CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
    CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"


For the ``celeryd`` systemd service put the following in ``/etc/systemd/system/celery.service`` and change ``WorkingDirectory`` to your dissemin root.::

    [Unit]
    Description=Celery service
    After=network.target

    [Service]
    Type=forking
    User=dissemin
    Group=dissemin
    Restart=always
    EnvironmentFile=-/etc/default/celery
    WorkingDirectory=/path/to/dissemin/
    ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} multi start ${CELERYD_NODES} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'
    ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait ${CELERYD_NODES} --pidfile=${CELERYD_PID_FILE}'
    ExecReload=/bin/sh -c '${CELERY_BIN} multi restart ${CELERYD_NODES} -A ${CELERY_APP} --pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} ${CELERYD_OPTS}'

    [Install]
    WantedBy=multi-user.target

For the ``celerybeatd`` systemd service put the following in ``/etc/systemd/system/celerybeat.service`` and change ``WorkingDirectory`` to your dissemin root.::

    [Unit]
    Description=Celerybeat service
    After=network.target

    [Service]
    Type=simple
    User=dissemin
    Group=dissemin
    Restart=always
    EnvironmentFile=-/etc/default/celery
    WorkingDirectory=/path/to/dissemin/
    ExecStart=/bin/sh -c 'PYTHONPATH=$(pwd) ${CELERY_BIN} -A ${CELERY_APP} beat --pidfile=${CELERYBEAT_PID_FILE} --logfile=${CELERYBEAT_LOG_FILE} --loglevel=${CELERYD_LOG_LEVEL} -s ${CELERYBEAT_SCHEDULE_FILE}'
    ExecStop=/bin/kill -s TERM $MAINPID

    [Install]
    WantedBy=multi-user.target

Note that we use ``/bin/sh -c`` to process the ``PYTHONPATH`` and ``${CELERY_BIN}``.

To make systemd create the necessary directories with permissions put the follwing into ``/etc/tmpfiles.d/celery.conf``::

    d /var/run/celery 0755 dissemin dissemin
    d /var/log/celery 0755 dissemin dissemin

After that run ``systemctl daemon-reload`` to reload systemd service files and you are ready to use ``celery`` and ``celerybeat`` with systemd by calling::

    systemctl start celery.service
    systemctl start celerybeat.service

To make them start on boot call::

    systemctl enable celery.service
    systemctl enable celerybeat.service

Logrotate
~~~~~~~~~

Over time the logfiles of celery tend to get rather big, so you should enable log rotation.
Celery does not complain if the log file is removed, it just opens it again.
