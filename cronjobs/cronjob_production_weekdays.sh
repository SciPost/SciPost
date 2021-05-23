#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.8.5/bin/activate

python manage.py send_refereeing_reminders --settings=SciPost_v1.settings.production_do1
