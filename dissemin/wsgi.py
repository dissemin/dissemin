"""
WSGI config for dissemin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys
print 'IMPORTING', __name__, 'from', __file__, 'in', os.getpid()
sys.path.append('/opt/dissemin')
sys.path.append('/home/pintoch/cam/.virtualenv/lib/python2.7/site-packages')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dissemin.settings")
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
