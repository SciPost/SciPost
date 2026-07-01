#!/bin/bash

# Monthly cronjobs for production area (start of the month)

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

python manage.py email_worklogs_to_HR --settings=SciPost_v1.settings.production_do1

# Archive and send any new issue/journal material to CLOCKSS
python manage.py archive_to_clockss --settings=SciPost_v1.settings.production_do1