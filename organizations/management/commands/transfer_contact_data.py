__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from partners.models import Partner

from organizations.models import Contact, ContactRole


class Command(BaseCommand):
    help = ('For Partners, transfer the data of partners.Contact instances '
            'to organizations.Contact and ContactRole instances.')

    def handle(self, *args, **kwargs):
        for partner in Partner.objects.all():
            for oldcontact in partner.contact_set.all():
                contact = Contact(
                    user=oldcontact.user,
                    title=oldcontact.title,
                    activation_key=oldcontact.activation_key,
                    key_expires=oldcontact.key_expires
                )
                contact.save()
                contactrole = ContactRole(
                    contact=contact,
                    organization=partner.organization,
                    kind=oldcontact.kind,
                    date_from=timezone.now(),
                    date_until=timezone.now() + datetime.timedelta(days=3650)
                )
                contactrole.save()
                oldcontact.delete()
