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
        u'UNIVERSITY_SHORT_NAME_WITHOUT_DETERMINER': u"ENS",
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
# 
# This interface should at least support fetching metadata for one
# single DOI, like this:
# curl -LH "Accept: application/citeproc+json" http://DOI_PROXY_DOMAIN/10.1080/15568318.2012.660115
# (returns the citation as Citeproc+JSON)
#
DOI_PROXY_DOMAIN =  'doi-cache.ulminfo.fr' # This acts as a caching proxy for dx.doi.org
#
# In addition, if the endpoint supports it, batch requests can be performed:
# curl -d 'dois=["10.1016/j.physletb.2015.01.010","10.5380/dp.v1i1.1922","10.1007/978-3-319-10936-7_9"]' \\
#        http://doi-cache.ulminfo.fr/batch
# (returns a list of citation in Citeproc+JSON format)
#
DOI_PROXY_SUPPORTS_BATCH = True

### RoMEO proxy ###
# Set this to 'sherpa.ac.uk' if our custom mirror is not up anymore.
# Otherwise our proxy caches results and is more reliable than the original endpoint.
ROMEO_API_DOMAIN = 'romeo-cache.ulminfo.fr'

### Paper deposits ###
# Max size of the PDFs (in bytes)
# 2.5MB - 2621440
# 5MB - 5242880
# 10MB - 10485760
# 20MB - 20971520
# 50MB - 5242880
DEPOSIT_MAX_FILE_SIZE = 10485760
# Max download time when the file is downloaded from an URL (in seconds)
URL_DEPOSIT_DOWNLOAD_TIMEOUT = 10
# Allowed content types
DEPOSIT_CONTENT_TYPES = ['application/pdf','application/x-pdf','application/octet-stream','application/x-download']

# Uncomment these settings if you rather want
# to fetch metadata directly from CrossRef (slower as not cached,
# and more requests as there is no batch support).
#DOI_PROXY_DOMAIN =  'dx.doi.org'
#DOI_PROXY_SUPPORTS_BATCH = False

### Security key ###
# This is used by django to generate various things (mainly for 
# authentication). Just pick a fairly random string and keep it
# secret.
SECRET_KEY = '40@!t4mmh7325-^wh+jo3teu^!yj3lfz5p%ok(8+7th8pg^hy1'

### Debug mode ###
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# This can safely (and should) be kept to True
TEMPLATE_DEBUG = True

### Allowed hosts ###
# They are the domains under which your dissemin instance should
# be reachable
ALLOWED_HOSTS = ['localhost']


### Central Authentication System ###
# This is used to authenticate your users.
# You only have to provide the URL of your CAS system and users
# will automatically be redirected to this page to log in from dissemin.
# Therefore no account creation is needed!
CAS_SERVER_URL="https://sso.ens.fr/cas/login"    #CRI CAS

# When logging out from dissemin, should we also log out from the CAS?
CAS_LOGOUT_COMPLETELY = True
# Should we provide a redirect URL to the CAS so that unlogged users
# can come back to dissemin?
CAS_PROVIDE_URL_TO_LOGOUT = True

### Application definition ###
# You should not have to change anything in this section.

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.orcid',
    'statistics',
    'publishers',
    'papers',
    'upload',
    'deposit',
    'bootstrap_pagination',
#    'debug_toolbar',
)

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
#    'django_cas_ng.middleware.CASMiddleware',
)


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
   # 'django_cas_ng.backends.CASBackend',
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
    'allauth.account.context_processors.account',
    'allauth.socialaccount.context_processors.socialaccount',
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    )),
)

ROOT_URLCONF = 'dissemin.urls'

WSGI_APPLICATION = 'dissemin.wsgi.application'


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
# https://docs.djangoproject.com/en/1.7/topics/cache/
CACHES = {
        'default': {
# This one is only suitable for developpment
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'my-cache'
# This one should be used in production
#            'BACKEND':'django.core.cache.backends.memcached.MemcachedCache',
#            'LOCATION':'127.0.0.1:11211',
    }
}

### Static files (CSS, JavaScript, Images) ###
# This defines how static files are stored and accessed.
# https://docs.djangoproject.com/en/1.6/howto/static-files/
#
# Absolute path to where the static files are stored.
# This is what you should change!
STATIC_ROOT = '/opt/dissemin/www/static/'
# Relative URL where static files are accessed (you should not
# need to change this).
STATIC_URL = '/static/'

# Relative path to the directory where we store user uploads
MEDIA_ROOT = 'media/'
MEDIA_URL = '/media/'

### Celery config ###
# Celery runs asynchronous tasks such as metadata harvesting or
# complex updates.
# To communicate with it, we need a "broker".
# This is an example broker with Redis.
BROKER_URL = 'redis://localhost:6379/0'
# For a RabbitMQ setting: BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672//'

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
CELERY_IMPORTS = ['backend.tasks']

# This is the time in seconds before an unacknowledged task is re-sent to
# another worker. It should exceed the length of the longest task, otherwise
# it will be executed twice ! 43200 is one day.
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 43200}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = ('locale',)

# Login and athentication
LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'


