#!/bin/bash

# Per hour cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

# Do tasks
python manage.py check_celery --settings=SciPost_v1.settings.production_do1
python manage.py advance_git_repos --settings=SciPost_v1.settings.production_do1

# Do a update_index of the last hour
python manage.py update_index -r -v 0 -a 1 --settings=SciPost_v1.settings.production_do1

# Run PubFrac compensations algorithm
python manage.py compensate_pubfracs --settings=SciPost_v1.settings.production_do1