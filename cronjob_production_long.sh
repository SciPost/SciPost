#!/bin/bash

# Long period (days) cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

./manage.py remind_fellows_to_submit_report
