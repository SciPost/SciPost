#!/bin/bash

# Per 5-minute cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

# Process the next submission for coauthorships with fellows
python manage.py update_fellow_submission_coauthorships --settings=SciPost_v1.settings.production_do1
