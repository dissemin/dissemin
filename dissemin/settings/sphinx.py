"""
Development specific settings for Dissemin project.
"""

import os

from .common import *

DEBUG = False

# They are the domains under which your dissemin instance should
# be reachable. Leave empty if you run on localhost.
ALLOWED_HOSTS = []

# Cache backend
# https://docs.djangoproject.com/en/1.8/topics/cache/
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

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

