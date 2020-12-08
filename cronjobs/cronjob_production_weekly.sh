#!/bin/bash

# Weekly cronjobs for production area

cd /home/scipost/SciPost
source venv-3.8.5/bin/activate

python manage.py email_fellows_tasklist --settings=SciPost_v1.settings.production_do1
