__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from guardian.shortcuts import assign_perm

from partners.models import Partner

from organizations.models import Contact, ContactRole


class Command(BaseCommand):
    help = ('For Partners, transfer the data of partners.Contact instances '
            'to organizations.Contact and ContactRole instances. '
            'This is meant as a temporary, one-off method to be used during '
            'deprecation of (Prospective)Partners.')

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

                # Assign permissions and Group
                assign_perm('can_view_org_contacts', oldcontact.user, partner.organization)
                orgcontacts = Group.objects.get(name='Organization Contacts')
                oldcontact.user.groups.add(orgcontacts)

                contactrole = ContactRole(
                    contact=contact,
                    organization=partner.organization,
                    kind=oldcontact.kind,
                    date_from=timezone.now(),
                    date_until=timezone.now() + datetime.timedelta(days=3650)
                )
                contactrole.save()
                oldcontact.delete()
