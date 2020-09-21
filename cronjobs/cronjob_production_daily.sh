#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/webapps/scipost_py38/SciPost
source ../venv3.8/bin/activate

python manage.py organization_update_cf_nr_associated_publications --settings=SciPost_v1.settings.production
