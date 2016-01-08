#!/bin/bash
source .virtualenv/bin/activate
python manage.py test --testrunner dissemin.scripts.baretests.BareTestRunner --settings dissemin.testsettings $@
