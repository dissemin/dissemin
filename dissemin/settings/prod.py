"""
Production specific settings for dissem.in

Optimized for performance.
"""

from .common import *

# Double-check your production configuration, always before deployment.
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

DEBUG = False

# They are the domains under which your dissemin instance should
# be reachable
ALLOWED_HOSTS = ['dissem.in']

# Cache backend
# https://docs.djangoproject.com/en/1.8/topics/cache/
CACHES = {
        'default': {
# This one uses Redis, which is already required for message-passing to Celery, so let's use it as a cache too
             'BACKEND':'redis_cache.RedisCache',
             'LOCATION':('%s:%d' % (REDIS_HOST,REDIS_PORT)),
             'OPTIONS': {
                 'DB':REDIS_DB,
                 'PASSWORD':REDIS_PASSWORD,
             },
    }
}

# ORCiD provider configuration (production)
SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
         # Base domain of the API. Default value: 'orcid.org', for the production API
        'BASE_DOMAIN':'orcid.org', # for the production API.
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False, # for the member API
       }
   }

### Static files (CSS, JavaScript, Images) ###
# This defines how static files are stored and accessed.
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# Absolute path to where the static files are stored.
# This is what you should change!
STATIC_ROOT = '/home/dissemin/dissemin/www/static/'
# Absolute path to the directory where we store user uploads
# This is what you should change!
MEDIA_ROOT = '/home/dissemin/dissemin/media/'

