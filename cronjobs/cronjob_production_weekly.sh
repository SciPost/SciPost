#!/bin/bash

# Weekly cronjobs for production area

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

python manage.py email_fellows_tasklist --settings=SciPost_v1.settings.production
