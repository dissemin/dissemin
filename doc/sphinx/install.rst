Installation
============

dissem.in is split in two parts: - the web frontend, powered by Django -
the tasks backend, powered by Celery

Installing the tasks backend requires additional dependencies and is not
necessary if you want to do light dev that does not require harvesting
metadata or running author disambiguation.

Installation instructions for the web frontend
---------------------

First, install the following dependencies (debian packages)
``postgresql postgresql-server-dev-all postgresql-client python-virtualenv build-essential libxml2-dev libxslt1-dev python-dev gettext``

Then, build a virtual environment to isolate all the python
dependencies::

   virtualenv .virtualenv
   source .virtualenv/bin/activate
   pip install -r requirements_frontend.txt

Set up the database
-------------------

Choose a unique database and user name (they can be identical), such as
``disseminENS``. Choose a strong password for your user (such as the
output of ``date | md5sum``)::

   sudo su postgres
   psql
   CREATE USER dissemin_ens WITH PASSWORD 'b3a55787b3adc3913c2129205821765d';
   ALTER USER dissemin_ens CREATEDB;
   CREATE DATABASE dissemin_ens WITH OWNER dissemin_ens;

Configure the settings
----------------------

Edit ``dissemin/settings.py`` to change the following settings: -
``CORE_API_KEY`` and ``ROMEO_API_KEYS`` are required if you want to
import papers automatically from these sources. See [[this
page\|apikeys]] to learn how to get them. - Create a fresh
``SERCET_KEY`` (any random-looking string that you can keep secret will
do) - Fill the DATABASE section with the details you chose in the
previous step - Set up the URL of your Central Authentication System in
``CAS_URL`` - Set up the SMTP parameters to send emails to authors, in
the ``EMAIL`` section. - Create a ``www/static`` directory and set the
``STATIC_ROOT`` variable to the global path for this folder.

You should commit these changes on a separate branch, let's call it
``prod``::

   git checkout -b prod
   git add dissemin/settings.py
   commit -m "Production settings"

Create the database structure
-----------------------------

This is done by applying migrations::

   python manage.py migrate auth
   python manage.py migrate

(this should be done every time the source code is updated).
Then you can move on to [[running the web server\|server]].

Optional: installing the tasks backend
-----------------------------------

The backend communicates with the frontend through a message passing
infrastructure. TODO: link to the Django doc for that.
We recommend redis.
TODO: update the rest of the doc
The default
settings are configured to use RabbitMQ, an AMQP server::
   apt-get install rabbitmq-server

(this launches the rabbitmq server). Install Python dependencies::

   sudo apt-get install libxml2 python-dev libxslt-dev liblapack-dev gfortran libopenblas-dev
   source .virtualend/bin/activate
   pip install -r requirements_backend.txt

Optional python dependencies (if you want to debug the learning system)::
   pip install nltk
   pip install matplotlib

To run the backend (still in the virtualenv)::
   celery --app=dissemin.celery:app worker -B -l INFO



