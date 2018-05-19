#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

python3 manage.py remind_fellows_to_submit_report
python3 manage.py send_refereeing_reminders
