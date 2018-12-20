#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

# Do tasks
python3 manage.py check_celery
python3 manage.py update_coi_via_arxiv
