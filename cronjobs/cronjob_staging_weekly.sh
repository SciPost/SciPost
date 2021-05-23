#!/bin/bash

# Weekly cronjobs for staging area

cd /home/scipost/SciPost/scipost_django
source ../venv3.8/bin/activate

python manage.py email_fellows_tasklist
