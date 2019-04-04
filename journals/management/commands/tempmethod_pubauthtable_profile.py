__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from journals.models import PublicationAuthorsTable


class Command(BaseCommand):
    help = ('Populates the profile field of PublicationAuthorsTable '
            'from the existing unregistered_author or contributor fields.')

    def handle(self, *args, **kwargs):
        """
        This temporary method populates the profile field of PublicationAuthorsTable.

        In preparation for deletion of the model's fields
        ``unregistated_author`` and ``contributor``.
        """
        ndone = 0
        for table in PublicationAuthorsTable.objects.all():
            if table.unregistered_author:
                if table.unregistered_author.profile:
                    table.profile = table.unregistered_author.profile
                    table.save()
                    ndone += 1
                if not table.profile:
                    print("Alert: no profile for table %s, id %i, UnregAuth id %i" % (
                        table, table.id, table.unregistered_author.id))
            elif table.contributor:
                if table.contributor.profile:
                    table.profile = table.contributor.profile
                    table.save()
                    ndone += 1
                if not table.profile:
                    print("Alert: no profile for table %s, id %i, Contributor id %i" % (
                        table, table.id, table.contributor.id))
        print("Number of tables updated: %i" % ndone)
