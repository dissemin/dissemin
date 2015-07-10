# -*- encoding: utf-8 -*-

# Dissemin: open access policy enforcement tool
# Copyright (C) 2014 Antonin Delpeuch
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#


"""
Django settings for dissemin project.

See the doc for details of usage:
http://dissemin.readthedocs.org/en/latest/install.html

For the full list of Django settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

### University names. ###
# This is used at various places to name the university.
# The URLs are not pointing to any special interface, they are only used
# to redirect users to the relevant websites.
UNIVERSITY_BRANDING = {
        u'UNIVERSITY_FULL_NAME': u'École Normale Supérieure',
        u'UNIVERSITY_SHORT_NAME': u"l'ENS",
        u'UNIVERSITY_REPOSITORY_URL': u'http://hal-ens.archives-ouvertes.fr/',
        u'UNIVERSITY_URL': u'http://www.ens.fr/',
}

### Emailing settings ###
# These are used to send messages to the researchers.
# This is still a very experimental feature. We recommend you leave these
# settings as they are for now.
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True

### API keys ###
# These keys are used to communicate with various interfaces. See
# http://dissemin.readthedocs.org/en/latest/apikeys.html 

# RoMEO API KEY
# Used to fetch publisher policies. Get one at
# http://www.sherpa.ac.uk/romeo/apiregistry.php
ROMEO_API_KEY = None

# CORE API key
# Used to fetch full text availability. Get one at
# http://www.sherpa.ac.uk/romeo/apiregistry.php
CORE_API_KEY = None

# Zenodo API key
# Used to upload papers. Get one at
# https://zenodo.org/youraccount/register
ZENODO_KEY = None

### DOI proxy ###
# The interface where to get DOI metadata from.
DOI_PROXY_DOMAIN =  'doi-cache.ulminfo.fr'
DOI_PROXY_SUPPORTS_BATCH = True
# Uncomment these settings if you rather want
# to fetch metadata directly from CrossRef (slower as not cached)
DOI_PROXY_DOMAIN =  'dx.doi.org'
DOI_PROXY_SUPPORTS_BATCH = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '40@!t4mmh7325-^wh+jo3teu^!yj3lfz5p%ok(8+7th8pg^hy1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'statistics',
    'publishers',
    'papers',
    'bootstrap_pagination',
#    'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_cas_ng.middleware.CASMiddleware',
)


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_cas_ng.backends.CASBackend',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    )),
)

ROOT_URLCONF = 'dissemin.urls'

WSGI_APPLICATION = 'dissemin.wsgi.application'

#CAS_SERVER_URL="https://localhost:8443/cas/login"    #Local tomcat CAS
#CAS_SERVER_URL="https://cas.eleves.ens.fr/login"   #SPI CAS
CAS_SERVER_URL="https://sso.ens.fr/cas/login"    #CRI CAS
CAS_LOGOUT_COMPLETELY = True
CAS_PROVIDE_URL_TO_LOGOUT = True


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'dissemin',
        'USER': 'dissemin',
        'PASSWORD': 'dissemin',
        'HOST': 'localhost'
    }
}

# Cache backend
# This one is only suitable for developpment
CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'my-cache'
# This one should be used in production
#            'BACKEND':'django.core.cache.backends.memcached.MemcachedCache',
#            'LOCATION':'127.0.0.1:11211',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = ('locale',)

# Login and athentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/opt/dissemin/www/static/'

# User uploads
MEDIA_ROOT = 'media/'

# Celery config
BROKER_URL = 'redis://localhost:6379/0'

BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}
# This is the time in seconds before an unacknowledged task is re-sent to
# another worker. It should exceed the length of the longest task, otherwise
# it will be executed twice ! 43200 is one day.

# RabbitMQ setting: BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672//'
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_IMPORTS = ['backend.tasks']
