#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.8.5/bin/activate

# Mails waiting in the database
python manage.py send_mails --settings=SciPost_v1.settings.production_do1
