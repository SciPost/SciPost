#!/bin/bash

# Monthly cronjobs for production area (start of the month)

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

python manage.py email_worklogs_to_HR --settings=SciPost_v1.settings.production_do1

# Anonymize and delete the reports of published papers
python manage.py anonymize_reports_long_term --limit 500 --settings=SciPost_v1.settings.production_do1