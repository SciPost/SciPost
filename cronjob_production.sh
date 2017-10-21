#!/bin/bash

cd /home/jscaux/webapps/scipost/SciPost_v1/
export DJANGO_SETTINGS_MODULE='SciPost_v1.settings.production'

python3.5 manage.py remind_fellows_to_submit_report
