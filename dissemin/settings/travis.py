"""
Travis specific settings for tests
"""

import os

# Patch urllib3 because the default SSL module on Travis sucks
import urllib3.contrib.pyopenssl

from .common import *

# We delete the logger 'dissemin', so that it goes to root logger and gets catched by pytest caplog fixture
del LOGGING['loggers']['dissemin']

# They are the domains under which your Dissemin instance should
# be reachable.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Cache backend
# https://docs.djangoproject.com/en/1.8/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': ('%s:%d' % (REDIS_HOST, REDIS_PORT)),
        'OPTIONS': {
            'DB': REDIS_DB,
            'PASSWORD': REDIS_PASSWORD,
        },
    }
}

if 'ROMEO_API_KEY' in os.environ:
    ROMEO_API_KEY = os.environ['ROMEO_API_KEY']

# Relative path from the project to store the uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'dissemin_media')

# Travis settings
# taken from https://gist.github.com/ndarville/3625246
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql_psycopg2',
        'NAME':     'dissemin',
        'USER':     'postgres',
        'PASSWORD': '',
        'HOST':     'localhost',
        'PORT':     '',
        'DISABLE_SERVER_SIDE_CURSORS': False,
    }
}

# Base domain of the ORCiD API.
ORCID_BASE_DOMAIN = 'orcid.org'  # our test dump uses identifiers from the production

# ORCiD provider configuration (sandbox)
SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
        'BASE_DOMAIN': ORCID_BASE_DOMAIN,
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False,  # for the member API
       }
    }

# Mock Celery (run tasks directly in the main process)
CELERY_ALWAYS_EAGER = True

# Debug Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

urllib3.contrib.pyopenssl.inject_into_urllib3()

# Some settings for SASS
# Set to tmp_static, so that test on CI find compiled static files
SASS_PROCESSOR_ROOT = os.path.join(BASE_DIR, 'tmp_static')
# Enable SASS processor to on the fly compile scss; mainly to have same test for dev and CI
SASS_PROCESSOR_ENABLED = True
# Output should be readable
SASS_OUTPUT_STYLE = 'nested'
# Static root must be set to have scss compile correctly
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# We need to set a redirect
SHIB_DS_SP_URL = 'https://shibboleth.dissem.in/'
# We need a DiscoFeed, otherwise the module does not work
SHIB_DS_DISCOFEED_PATH = os.path.join(BASE_DIR, 'test_data', 'shibds', 'DiscoFeed.json')
