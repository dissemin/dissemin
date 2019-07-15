.. _page-deploying:

Deploying dissemin
==================

You have two options to run the web server: development or production
settings.

Development settings
--------------------

Simply run ``./launch.sh``. This uses the default Django server (unsuitable
for production) and serves the website locally on the port 8080. Note that the standard port for django-admins runserver-command is _8000_, but this ensures compatibility with the Vagrant installation.

This runs with ``DEBUG = True``, which means that Django will report to the user
any internal error in a transparent way. This is useful to debug your installation
but should not be used for production as it exposes your internal settings.

Production settings
-------------------

As any Django website, Dissemin can be served by various web servers.
These settings are not specific to dissemin itself so you should refer
to `the relevant Django documentation <https://docs.djangoproject.com/en/2.2/howto/deployment/>`_.

No matter what web server you use,
you need to run ``python manage.py collectstatic`` to copy the static files from
the git repository to the desired location for your installation (in the example below,
``/home/dissemin/www/static``), as well as ``python manage.py compilemessages`` to compile
the translation files.

Make sure that your `media/` directory is writable by the user under which the application will run
(`www-data` on Debian).

Self-hosting MathJax
--------------------

Dissemin requires `MathJax <https://www.mathjax.org/>`_ for rendering LaTeX
formatting in the abstracts. Out of the box, Dissemin will use a CDN-hosted
version of MathJax. This has the downside of `preventing deposit when disabling
third-party JS <https://github.com/dissemin/dissemin/issues/454>`_.

An easy solution to this is to self-host MathJax. You can follow the
`installation instructions
<https://docs.mathjax.org/en/latest/start.html#downloading-and-installing-mathjax>`_
from MathJax to get a local copy. Ideally, you should put it in the static
directory (under ``/home/dissemin/www/static/`` in the example below).

Note that MathJax consists of many small files which can slow down a lot the
built-in Django webserver. Hence, it is better to serve it directly by Apache
and avoid having all these files in the ``papers/static/libs`` directory of
Dissemin.

Once MathJax is downloaded and available by your webserver, you can use the
setting ``MATHJAX_SELFHOST_URL`` (in ``dissemin/settings``) to specify a location
to load MathJax from. In the example below, this would be
``//dissemin.myuni.edu/static/mathjax/MathJax.js?config=TeX-AMS-MML_HTMLorMML``.

Apache with WSGI
----------------

A sample VirtualHost, assuming that the root of the Dissemin source code is at ``/home/dissemin/prod`` and you use a ``python3.5`` virtualenv is available in the `Dissemin Git repository <https://github.com/dissemin/dissemin/blob/master/provisioning/apache2-vhost.conf` (under ``provisioning/apache2-vhost.conf``).


You should only have to change the path to the application and the domain name of the service.


lighttpd with FastCGI (deprecated)
----------------------------------

We describe here how to set up the server with lighttpd, a lightweight
web server, with FastCGI. This has been deprecated by Django, as support
for FastCGI will be discontinued: use WSGI instead.

Add this to your lighttpd config::

   $HTTP["host"] =~ "^myhostname.com$" {
       accesslog.filename   = "/var/log/lighttpd/dissemin-$INSTANCE.log"
       server.document-root = "$SOURCE_PATH/www/"
       $HTTP["url"] =~ "^(?!((/static/)|(/robots\.txt)))" {
           fastcgi.server = (
               "/" => (
                   "/" => (
                       "socket" => "/tmp/django-dissemin-$INSTANCE.sock",
                       "check-local" => "disable",
                       "fix-root-scriptname" => "enable",
                   )
               ),
           )
       }
       alias.url = (
           "/static/" => "$SOURCE_PATH/www/static/",
           "/robots.txt" => "$SOURCE_PATH/www/static/robots.txt",
       )
   }

where ``$INSTANCE`` is the name of your instance and ``$SOURCE_PATH`` is
the path to the root of the git repository of dissemin.

You can create the ``.sock`` file with
``touch /tmp/django-dissemin-$INSTANCE.sock``.
