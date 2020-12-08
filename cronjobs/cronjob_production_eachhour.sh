#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/SciPost
source venv-3.8.5/bin/activate

# Do tasks
python manage.py check_celery --settings=SciPost_v1.settings.production_do1
python manage.py update_coi_via_arxiv --settings=SciPost_v1.settings.production_do1

# Do a update_index of the last hour
python manage.py update_index -r -v 0 -a 1 --settings=SciPost_v1.settings.production_do1
