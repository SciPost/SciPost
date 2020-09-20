#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

# Do tasks
python manage.py check_celery
python manage.py update_coi_via_arxiv

# Do a update_index of the last hour
python manage.py update_index -r -v 0 -a 1
