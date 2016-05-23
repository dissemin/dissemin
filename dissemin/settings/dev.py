"""
Development specific settings for Dissemin project.
"""

from .common import *
import os

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

# Base domain of the ORCiD API.
ORCID_BASE_DOMAIN = 'sandbox.orcid.org' # for the sandbox API

# ORCiD provider configuration (sandbox)
SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
        'BASE_DOMAIN': ORCID_BASE_DOMAIN,
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False, # for the member API
       }
   }


# Debug Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relative path from the project to store the uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'dissemin_media')

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
    },
}

# Disable caching in dev
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request"
            ),
            'debug': True
        }
    }
]
