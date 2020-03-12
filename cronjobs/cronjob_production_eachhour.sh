#!/bin/bash

# Per minute cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

# Do tasks
python3 manage.py check_celery
python3 manage.py update_coi_via_arxiv

# Do a update_index of the last hour
python3 manage.py update_index -r -v 0 -a 1
