#!/bin/bash

# Weekly cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

python manage.py email_fellows_tasklist --settings=SciPost_v1.settings.production_do1
