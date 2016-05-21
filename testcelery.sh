#!/bin/bash

if [ ! -e dissemin/settings/test.py ]; then
    echo "To run the tests, please create first a settings file at dissemin/settings/test.py."
    echo "You can use an existing settings file (by importing it),"
    echo "but be aware that running the tests will flush the database."
    exit 1
fi


source .virtualenv/bin/activate
DJANGO_SETTINGS_MODULE="dissemin.settings.test" celery --app=dissemin.testcelery:app worker -B -l INFO
