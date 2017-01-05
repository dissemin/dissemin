#!/bin/bash
python manage.py dumpdata --format json --natural-foreign -e contenttypes -e auth -o papers/fixtures/test_dump.json
