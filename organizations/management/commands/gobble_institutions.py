__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from affiliations.models import Affiliation as deprec_Affiliation
from affiliations.models import Institution
from organizations.models import Organization
from profiles.models import Affiliation


class Command(BaseCommand):
    help = ('For affiliations.Institution objects with a defined organization '
            'field, update the user Profiles to the new profiles.Affiliation objects '
            'and delete the deprecated Institution and Affiliation objects.')

    def handle(self, *args, **kwargs):
        for inst in Institution.objects.exclude(organization=None):
            print('Handling institution %s' % str(inst))
            for deprec_aff in deprec_Affiliation.objects.filter(institution=inst):
                Affiliation.objects.create(
                    profile=deprec_aff.contributor.profile,
                    organization=deprec_aff.institution.organization,
                    date_from=deprec_aff.begin_date,
                    date_until=deprec_aff.end_date)
                print('\t\tDeleting affiliation %s' % str(deprec_aff))
                deprec_aff.delete()
            print('\tDeleting institution %s' % str(inst))
            inst.delete()
