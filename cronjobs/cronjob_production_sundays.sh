#!/bin/bash

# Weekly cronjobs for production area
# Weekend jobs

cd /home/scipost/SciPost
source venv-3.8.5/bin/activate

python manage.py update_citedby --settings=SciPost_v1.settings.production_do1

python manage.py journal_update_cf_metrics  --settings=SciPost_v1.settings.production_do1

# Do a full update_index when maybe something has slipped through during the week
python manage.py update_index -r -v 0 --settings=SciPost_v1.settings.production_do1
