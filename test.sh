#!/bin/bash
source .virtualenv/bin/activate
export DJANGO_SETTINGS_MODULE="dissemin.testsettings"
python manage.py flush --noinput
python manage.py loaddata dissemin/fixtures/test_dump.json
python manage.py test --testrunner dissemin.scripts.baretests.BareTestRunner $@
