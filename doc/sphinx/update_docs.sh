#!/bin/bash

DESTINATION="/var/www/dev.dissem.in/"

source .venv/bin/activate
make -B doc
cd doc/sphinx
make html
cd ../../
rsync -av doc/sphinx/_build/html/ "$DESTINATION"

