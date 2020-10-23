#!/bin/bash

# Daily cronjobs for staging area

cd /home/scipoststg/webapps/scipost/scipost_v1
source venv3.8/bin/activate

python manage.py remind_fellows_to_submit_report
