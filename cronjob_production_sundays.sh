#!/bin/bash

# Weekly cronjobs for production area
# Weekend jobs

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

python3 manage.py update_citedby
