#!/bin/bash

# update translations, report missing and fuzzy translations

if [ -z "$TRAVIS" ]; then
    # go into directory of script
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    cd "$DIR"

    git pull -q
fi

python manage.py makemessages -l fr >&2
msggrep -v -T -e '.' locale/fr/LC_MESSAGES/django.po
awk -v RS='' '/#, fuzzy/' locale/fr/LC_MESSAGES/django.po

