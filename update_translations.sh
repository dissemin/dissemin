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
# fuzzy translations are in a paragraph containing #, fuzzy
# but we must exclude those where msgstr is itself commented out
# (it is at BOL when not commented out, and preceded by a space otherwise)
awk -v RS='' '/#, fuzzy.*[^ ]msgstr/' locale/fr/LC_MESSAGES/django.po

