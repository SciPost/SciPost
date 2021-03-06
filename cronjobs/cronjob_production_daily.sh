#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.8.5/bin/activate

python manage.py organization_update_cf_associated_publication_ids --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_nr_associated_publications --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_expenditure_for_publication --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_balance_info --settings=SciPost_v1.settings.production_do1

python manage.py affiliatejournal_update_publications_from_Crossref --settings=SciPost_v1.settings.production_do1
