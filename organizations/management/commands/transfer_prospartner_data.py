__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from partners.models import ProspectivePartner

from organizations.models import OrganizationEvent, ContactPerson


class Command(BaseCommand):
    help = ('For ProspectivePartners with a filled-in organization field, '
            'transfer the data from ProspectiveContact to ContactPerson, '
            'and ProspectivePartnerEvent to OrganizationEvent.')

    def handle(self, *args, **kwargs):
        for prospartner in ProspectivePartner.objects.filter(
                organization__isnull=False):
            for proscontact in prospartner.prospective_contacts.all():
                contact = ContactPerson(
                    organization=prospartner.organization,
                    title=proscontact.title,
                    first_name=proscontact.first_name,
                    last_name=proscontact.last_name,
                    email=proscontact.email,
                    role=proscontact.role)
                contact.save()
                proscontact.delete()
            oldman = User.objects.get(email='J.S.Caux@uva.nl')
            for prosevent in prospartner.prospectivepartnerevent_set.all():
                if prosevent.noted_by:
                    noted_by = prosevent.noted_by.user
                else:
                    noted_by = oldman
                event = OrganizationEvent(
                    organization=prospartner.organization,
                    event=prosevent.event,
                    comments=prosevent.comments,
                    noted_on=prosevent.noted_on,
                    noted_by=noted_by)
                event.save()
                prosevent.delete()
            prospartner.delete()
