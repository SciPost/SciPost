__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.management.base import BaseCommand

from partners.models import Partner

from organizations.models import OrganizationEvent


class Command(BaseCommand):
    help = ('For Partners, transfer the data of partners.PartnerEvent instances '
            'to organizations.OrganizationEvent instances. '
            'This is meant as a temporary, one-off method to be used during '
            'deprecation of (Prospective)Partners.')

    def handle(self, *args, **kwargs):
        for partner in Partner.objects.all():
            for partnerevent in partner.events.all():
                event_kind = 'comment'
                if partnerevent.event == 'initial':
                    event_kind = 'email_sent'
                elif partnerevent.event == 'status_update':
                    event_kind = 'status_updated'
                event = OrganizationEvent(
                    organization=partner.organization,
                    event=event_kind,
                    comments=partnerevent.comments,
                    noted_on=partnerevent.noted_on,
                    noted_by=partnerevent.noted_by)
                event.save()
                partnerevent.delete()
