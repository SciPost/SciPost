#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

python3 manage.py organization_update_cf_nr_associated_publications
