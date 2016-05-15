import os

# Travis settings
# taken from https://gist.github.com/ndarville/3625246
if 'TRAVIS' in os.environ:
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
    # Patch urllib3 because the default SSL module on Travis sucks
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()

if 'CORE_API_KEY' in os.environ:
    CORE_API_KEY = os.environ['CORE_API_KEY']

if 'ROMEO_API_KEY' in os.environ:
    ROMEO_API_KEY = os.environ['ROMEO_API_KEY']
