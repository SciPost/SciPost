#!/bin/bash

# Daily cronjobs for staging area

cd /home/scipost/SciPost/scipost_django
source ../venv3.11/bin/activate

python manage.py remind_fellows_to_submit_report
