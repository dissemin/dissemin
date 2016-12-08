.. _page-deploying:

Deploying dissemin
==================

You have two options to run the web server: development or production
settings.

Development settings
--------------------

Simply run ``./launch.sh``. This uses the default Django server (unsuitable
for production) and serves the website locally on the port 8080.

This runs with ``DEBUG = True``, which means that Django will report to the user
any internal error in a transparent way. This is useful to debug your installation
but should not be used for production as it exposes your internal settings.

Production settings
-------------------

As any Django website, Dissemin can be served by various web servers.
These settings are not specific to dissemin itself so you should refer
to `the relevant Django documentation <https://docs.djangoproject.com/en/1.8/howto/deployment/>`_.

No matter what web server you use,
you need to run ``python manage.py collectstatic`` to copy the static files from
the git repository to the desired location for your installation (in the example below,
``/home/dissemin/www/static``), as well as ``python manage.py compilemessages`` to compile
the translation files.

Make sure that your `media/` directory is writable by the user under which the application will run
(`www-data` on Debian).

Apache with WSGI
----------------

Here is a sample VirtualHost, assuming that the root of the Dissemin source code is at ``/home/dissemin``.::

    <VirtualHost *:80>
            ServerAdmin webmaster@localhost
            ServerName dissemin.myuni.edu
            
            ### STATIC FILES ###

            # Instructions for robots
            Alias /robots.txt /home/dissemin/www/static/robots.txt
            <Location /robots.txt>
            Require all granted
            </Location>
            # Favicon at the root
            Alias /favicon.ico /home/dissemin/www/static/favicon/favicon.ico
            <Location /favicon.ico>
            Require all granted
            </Location>
            # Thumbnails of PDF files uploaded by users
            Alias /media/thumbnails/ /home/dissemin/media/thumbnails/
            <Directory /home/dissemin/media/thumbnails>
            Require all granted
            </Directory>
            # Logos of the repositories configured on your instance
            Alias /media/repository_logos/ /home/dissemin/media/repository_logos/
            <Directory /home/dissemin/media/repository_logos>
            Require all granted
            </Directory>
            # Generic static files (CSS, JS, images)
            Alias /static/ /home/dissemin/www/static/
            <Directory /home/dissemin/www/static>
            Require all granted
            </Directory>
            # More detailed favicons
            Alias /favicon/ /home/dissemin/www/static/favicon/
            <Directory /home/dissemin/www/static/favicon>
            Require all granted
            </Directory>

            ### WSGI connection ###

            # Path to the WSGI application for the website
            WSGIScriptAlias / /home/dissemin/dissemin/wsgi.py
            # Python path for the application
            WSGIDaemonProcess dissemin.myuni.edu python-path=/home/dissemin:/home/dissemin/.virtualenv/lib/python2.7/site-packages

            WSGIProcessGroup dissemin.myuni.edu

            <Directory /home/dissemin/dissemin>
            <Files wsgi.py>
            Require all granted
            </Files>
            </Directory>

            ### Error handling ###
            ErrorDocument 500 /500-error
            ErrorDocument 404 /404-error

            ### Log settings ###
            ErrorLog ${APACHE_LOG_DIR}/django-dissemin-myuni.log

            # Possible values include: debug, info, notice, warn, error, crit,
            # alert, emerg.
            LogLevel debug

            CustomLog ${APACHE_LOG_DIR}/access-dissemin-myuni.log combined
    </VirtualHost>

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
