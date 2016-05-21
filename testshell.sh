#!/bin/bash
source .virtualenv/bin/activate
export DJANGO_SETTINGS_MODULE="dissemin.settings.test"
python manage.py shell
