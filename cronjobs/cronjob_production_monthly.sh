#!/bin/bash

# Monthly cronjobs for production area (start of the month)

cd /home/scipost/SciPost/scipost_django
source ../venv-3.11.7/bin/activate

python manage.py email_worklogs_to_HR --settings=SciPost_v1.settings.production_do1
