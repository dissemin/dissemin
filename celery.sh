#!/bin/bash
celery --app=dissemin.celery:app worker -B -l INFO
