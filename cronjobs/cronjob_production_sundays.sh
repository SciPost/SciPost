#!/bin/bash

# Weekly cronjobs for production area
# Weekend jobs

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

python manage.py update_citedby

# Do a full update_index when maybe something has slipped through during the week
python manage.py update_index -r -v 0
