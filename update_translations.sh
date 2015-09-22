#!/bin/bash

# update translations, report missing and fuzzy translations

# go into directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

git pull -q
python manage.py makemessages -l fr >&2
msggrep -v -T -e '.' locale/fr/LC_MESSAGES/django.po
awk -v RS='' '/#, fuzzy/' locale/fr/LC_MESSAGES/django.po

