#!/bin/bash
source .virtualenv/bin/activate

if [ ! -e dissemin/settings/test.py ]; then
    echo "To run the tests, please create first a settings file at dissemin/settings/test.py."
    echo "You can use an existing settings file (by importing it),"
    echo "but be aware that running the tests will flush the database."
    exit 1
fi

echo "Reminder:"
echo "Running the tests require a running Celery instance."
echo "You can start one with ./testcelery.sh"

export DJANGO_SETTINGS_MODULE="dissemin.settings.test"
python manage.py flush --noinput
python manage.py loaddata dissemin/fixtures/test_dump.json
python manage.py test --testrunner dissemin.scripts.baretests.BareTestRunner $@
