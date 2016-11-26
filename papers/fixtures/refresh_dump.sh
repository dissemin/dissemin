#!/bin/bash
python manage.py dumpdata --format json --natural-foreign -e contenttypes -e auth -o dissemin/fixtures/test_dump.json
