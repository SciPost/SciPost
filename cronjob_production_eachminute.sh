#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

# Mails waiting in the database
./manage.py send_mails
