.. _page-deploying:

Deploying dissemin
==================

You have two options to run the web server: development or production
settings.

Development settings
--------------------

Simply run ``./launch.sh``. This uses the default Django server (unsuitable
for production) and serves the website locally on the port 8000.

Production settings
-------------------

As any Django website, Dissemin can be served by various web servers.
These settings are not specific to dissemin itself so you should refer
to the relevant Django documentation.

We describe here how to set up the server with lighttpd, a lightweight
web server, with FastCGI.

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
