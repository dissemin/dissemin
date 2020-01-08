"""
Development specific settings for Dissemin project.
"""

import os

from .common import *

DEBUG = True
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda r: True}

# Set the log level with LOGLEVEL. If exists, this value is overwritten by the environment variable DISSEMIN_LOGLEVEL
LOGLEVEL = 'DEBUG'
LOGGING['loggers']['dissemin']['level'] = os.environ.get('DISSEMIN_LOGLEVEL', LOGLEVEL).upper()

# They are the domains under which your Dissemin instance should
# be reachable. Leave as is if you run on localhost.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# If you do not want to use Celery,
# use this setting to run all asynchronous tasks in the main process
# (celery will still be required as a dependency, but you do not need
# to run any other process, and no redis server).
# CELERY_ALWAYS_EAGER = True

# Cache backend
# https://docs.djangoproject.com/en/1.8/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

# Add Debug Toolbar
INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)


MIDDLEWARE += [
     'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Base domain of the ORCiD API.
ORCID_BASE_DOMAIN = 'sandbox.orcid.org'  # for the sandbox API

# ORCiD provider configuration (sandbox)
SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
        'BASE_DOMAIN': ORCID_BASE_DOMAIN,
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False,  # for the member API
       }
    }


# Debug Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relative path from the project to store the uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'dissemin_media')

# Set to tmp_static, so it does not pollute normal static folders
SASS_PROCESSOR_ROOT = os.path.join(BASE_DIR, 'tmp_static')
