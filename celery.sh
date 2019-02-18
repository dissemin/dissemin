#!/bin/bash
cd "$(dirname "$0")"
PYTHONPATH=$(pwd) celery --app=dissemin.celery:app worker -B -l INFO
