#!/bin/bash

# Weekly cronjobs for production area

cd /home/scipost/webapps/scipost/scipost_v1
source venv/bin/activate

./manage.py email_fellows_tasklist
