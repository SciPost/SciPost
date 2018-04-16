#!/bin/bash

# Weekly cronjobs for staging area

cd /home/scipoststg/webapps/scipost/scipost_v1
source venv/bin/activate

python manage.py email_fellows_tasklist
