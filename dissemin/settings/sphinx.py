"""
Django configuration for sphinx build.

Most settings are left empty or to their default values
as they are not actually used.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.join(
    os.path.dirname(__file__), '..', '..', '..'))

DEBUG = False

ALLOWED_HOSTS = []

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }
}

ORCID_BASE_DOMAIN = 'sandbox.orcid.org'  # for the sandbox API

SOCIALACCOUNT_PROVIDERS = \
   {'orcid':
       {
        'BASE_DOMAIN': ORCID_BASE_DOMAIN,
         # Member API or Public API? Default: False (for the public API)
         'MEMBER_API': False,  # for the member API
       }
    }


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MEDIA_ROOT = os.path.join(BASE_DIR, 'dissemin_media')

DEBUG = False
DATABASES = {}
EMAIL_HOST = None
EMAIL_HOST_PASSWORD = None
EMAIL_HOST_USER = None
EMAIL_USE_TLS = None
REDIS_DB = None
REDIS_HOST = None
REDIS_PASSWORD = None
REDIS_PORT = None
ROMEO_API_KEY = None
SECRET_KEY = '54eabc7548440450681f7b48daf688aca3800bda'

BASE_DIR = os.path.dirname(os.path.join(
    os.path.dirname(__file__), '..', '..', '..'))

DOI_PROXY_DOMAIN = 'doi-cache.dissem.in'
DOI_PROXY_SUPPORTS_BATCH = True

CROSSREF_MAILTO = 'dev@dissem.in'
CROSSREF_USER_AGENT = 'Dissemin/0.1 (https://dissem.in/; mailto:dev@dissem.in)'

ROMEO_API_DOMAIN = 'romeo-cache.dissem.in'

DEPOSIT_MAX_FILE_SIZE = 1024*1024*200  # 20 MB
URL_DEPOSIT_DOWNLOAD_TIMEOUT = 10

PROFILE_REFRESH_ON_LOGIN = timedelta(days=1)

INSTALLED_APPS = (
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'bootstrap3_datepicker',
    'rest_framework',
    'crispy_forms',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.orcid',
    'statistics',
    'publishers',
    'papers',
    'upload',
    'deposit',
    'deposit.zenodo',
    'deposit.hal',
    'deposit.osf',
    'autocomplete',
    'notification',
    'bootstrap_pagination',
    'django_js_reverse',
    'solo',
    'haystack',
    'widget_tweaks',
    'capture_tag',
    'memoize',
    'django_countries',
    'leaflet',
    'djgeojson',
    'raven.contrib.django.raven_compat'
)

CRISPY_TEMPLATE_PACK = 'bootstrap3'

SITE_ID = 1

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)


TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(BASE_DIR, 'templates')
            ],
            'OPTIONS': {
                'loaders': (
                    ('django.template.loaders.cached.Loader', (
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                    )),
                ),
                'context_processors': (
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.media",
                    "django.template.context_processors.static",
                    "django.template.context_processors.tz",
                    "django.template.context_processors.request",
                    "dissemin.tcp.orcid_base_domain",
                ),
                'debug': True
            }
        }
]

ROOT_URLCONF = 'dissemin.urls'

WSGI_APPLICATION = 'dissemin.wsgi.application'


STATIC_URL = '/static/'
MEDIA_URL = '/media/'

BROKER_URL = 'redis://'
CELERY_RESULT_BACKEND = BROKER_URL

redis_client = None

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_IMPORTS = ['backend.tasks']

CELERYBEAT_SCHEDULE = {
}

BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}

LANGUAGE_CODE = 'en-us'
POSSIBLE_LANGUAGE_CODES = ['en', 'fr', 'zh-hans', 'mk']
LANGUAGES = [
    ('en', 'English'),
]

TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = (os.path.join(BASE_DIR, 'locale'),)

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'PAGE_SIZE': 10,
    'DEFAULT_PAGINATION_CLASS':
    'rest_framework.pagination.LimitOffsetPagination', # silences useless warning
    'DEFAULT_RENDERER_CLASSES': (
                'rest_framework.renderers.JSONRenderer',
                'rest_framework.renderers.BrowsableAPIRenderer',
            ),
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'search.SearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'dissemin',
    },
}

DEPOSIT_NOTIFICATION_CALLBACK = (lambda payload: None)
