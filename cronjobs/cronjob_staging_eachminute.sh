#!/bin/bash

# Per minute cronjobs for staging area

cd /home/scipost/SciPost/scipost_django
source ../venv3.11/bin/activate

# Mails waiting in the database
python manage.py send_mails
# python manage.py mailgun_get_events --nr_minutes=2 --settings=SciPost_v1.settings.staging_do1
# python manage.py mailgun_get_stored_messages --settings=SciPost_v1.settings.staging_do1
# python manage.py mailgun_send_messages --settings=SciPost_v1.settings.staging_do1
