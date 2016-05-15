"""
Development specific settings for Dissemin project.
"""

from .common import *

DEBUG = True
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda r: True}

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
)

# ORCiD provider configuration (sandbox)
SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
         # Base domain of the API. Default value: 'orcid.org', for the production API
        'BASE_DOMAIN':'sandbox.orcid.org', # for the sandbox API
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False, # for the member API
       }
   }


# Debug Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relative path from the project to store the uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'dissemin_media')
