#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

python manage.py send_refereeing_reminders --settings=SciPost_v1.settings.production
