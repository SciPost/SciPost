#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

# Mails waiting in the database
python manage.py send_mails
