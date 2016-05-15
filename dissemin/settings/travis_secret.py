"""
Travis secrets for tests
"""

import os

if 'CORE_API_KEY' in os.environ:
    CORE_API_KEY = os.environ['CORE_API_KEY']

if 'ROMEO_API_KEY' in os.environ:
    ROMEO_API_KEY = os.environ['ROMEO_API_KEY']

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
    }
}
