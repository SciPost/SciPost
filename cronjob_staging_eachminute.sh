#!/bin/bash

# Per minute cronjobs for staging area

cd /home/scipoststg/webapps/scipost/scipost_v1
source venv/bin/activate

# Mails waiting in the database
python manage.py send_mails
