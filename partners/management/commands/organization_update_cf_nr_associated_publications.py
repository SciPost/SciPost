__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from partners.models import Organization


class Command(BaseCommand):
    help = ('For all Organization model instances, '
            'this updates the calculated field cf_nr_associated_publications')

    def handle(self, *args, **kwargs):
        for org in Organization.objects.all():
            org.update_cf_nr_associated_publications()
        self.stdout.write(self.style.SUCCESS(
            'Successfully updated Organization:cf_nr_associated_publications.'))
