#!/bin/bash

# Daily cronjobs for production area

cd /home/scipost/SciPost/scipost_django
source ../venv-3.13/bin/activate

python manage.py organization_update_cf_associated_publication_ids --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_nr_associated_publications --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_expenditure_for_publication --settings=SciPost_v1.settings.production_do1

python manage.py organization_update_cf_balance_info --settings=SciPost_v1.settings.production_do1

python manage.py affiliatejournal_update_publications_from_Crossref --settings=SciPost_v1.settings.production_do1


# Update the fellowship of submissions for new fellows
python manage.py update_submission_fellowships --settings=SciPost_v1.settings.production_do1

# Update the users' groups 
python manage.py update_user_permission_groups --settings=SciPost_v1.settings.production_do1

# Delete expired sessions (today's date implied)
python manage.py delete_expired_sessions --settings=SciPost_v1.settings.production_do1

# Update authors about their submissions in the assignment stage
python manage.py send_assignment_stage_update --settings=SciPost_v1.settings.production_do1

# Update pubfracs distribution
python manage.py compensate_pubfracs --settings=SciPost_v1.settings.production_do1