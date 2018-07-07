__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone
from django.urls import reverse

from django_countries.fields import CountryField

from .constants import ORGANIZATION_TYPES, ORGANIZATION_STATUSES, ORGSTATUS_ACTIVE

from .constants import (
    PARTNER_KINDS, PARTNER_STATUS, CONSORTIUM_STATUS, MEMBERSHIP_DURATION, PARTNER_EVENTS,
    PROSPECTIVE_PARTNER_STATUS, PROSPECTIVE_PARTNER_EVENTS, MEMBERSHIP_AGREEMENT_STATUS,
    PROSPECTIVE_PARTNER_ADDED, PARTNER_KIND_UNI_LIBRARY)
from .constants import (
    PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT, PROSPECTIVE_PARTNER_APPROACHED, PARTNER_INITIATED,
    PROSPECTIVE_PARTNER_EVENT_INITIATE_NEGOTIATION, PROSPECTIVE_PARTNER_PROCESSED, CONTACT_TYPES,
    PROSPECTIVE_PARTNER_NEGOTIATING, PROSPECTIVE_PARTNER_EVENT_MARKED_AS_UNINTERESTED,
    REQUEST_STATUSES, PROSPECTIVE_PARTNER_UNINTERESTED, PROSPECTIVE_PARTNER_EVENT_PROMOTED,
    REQUEST_INITIATED)

from .managers import (
    MembershipAgreementManager, ProspectivePartnerManager, PartnerManager, ContactRequestManager,
    PartnersAttachmentManager)

from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import get_sentinel_user, Contributor
from scipost.storage import SecureFileStorage

now = timezone.now()


#################
# Organizations #
#################

class Organization(models.Model):
    """
    An Organization instance is any type of administrative unit which SciPost
    can interact with. Example types include universities, funding agencies,
    research institutes etc.

    All instances can only be created by SciPost administration-level personnel,
    and can thus be considered as verified.

    These objects are meant to be internally linked to all other types of
    (possibly user-defined) objects used throughout the site (such as Institutions,
    Partners, Affiliations, Funders etc). This enables relating all of SciPost's
    services to the organizations which are impacted by its activities.

    The data here is also meant to be cross-linked to external databases,
    for example the Global Research Identifier Database (GRID), Crossref,
    ORCID etc.
    """
    orgtype = models.CharField(max_length=32, choices=ORGANIZATION_TYPES)
    status = models.CharField(max_length=32, choices=ORGANIZATION_STATUSES,
                              default=ORGSTATUS_ACTIVE)
    name = models.CharField(max_length=256,
                            help_text="Western version of name")
    name_original = models.CharField(max_length=256, blank=True,
                                     help_text="Name (in original language)")
    acronym = models.CharField(max_length=64, blank=True,
                               help_text='Acronym or short name')
    country = CountryField()
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organizations/logos/', blank=True)
    css_class = models.CharField(max_length=256, blank=True,
                                 verbose_name="Additional logo CSS class")
    grid_json = JSONField(default={}, blank=True, null=True) # JSON data from GRID
    crossref_json = JSONField(default={}, blank=True, null=True) # JSON data from Crossref
    superseded_by = models.ForeignKey('self', blank=True, null=True,
                                      on_delete=models.SET_NULL)

    def __str__(self):
        return self.name



########################
# Prospective Partners #
########################

class ProspectivePartner(models.Model):
    """A prospect Partner is a Partner without explicit contract with SciPost yet."""

    kind = models.CharField(max_length=32, choices=PARTNER_KINDS, default=PARTNER_KIND_UNI_LIBRARY)
    institution_name = models.CharField(max_length=256)
    country = CountryField()
    date_received = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, choices=PROSPECTIVE_PARTNER_STATUS,
                              default=PROSPECTIVE_PARTNER_ADDED)

    objects = ProspectivePartnerManager()

    def __str__(self):
        return '%s (received %s), %s' % (self.institution_name,
                                         self.date_received.strftime("%Y-%m-%d"),
                                         self.get_status_display())

    @property
    def is_promoted_to_partner(self):
        """Check if Prospect is already known to be a Partner."""
        return self.status == PROSPECTIVE_PARTNER_PROCESSED

    def update_status_from_event(self, event):
        if event == PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT:
            self.status = PROSPECTIVE_PARTNER_APPROACHED
        elif event == PROSPECTIVE_PARTNER_EVENT_INITIATE_NEGOTIATION:
            self.status = PROSPECTIVE_PARTNER_NEGOTIATING
        elif event == PROSPECTIVE_PARTNER_EVENT_MARKED_AS_UNINTERESTED:
            self.status = PROSPECTIVE_PARTNER_UNINTERESTED
        elif event == PROSPECTIVE_PARTNER_EVENT_PROMOTED:
            self.status = PROSPECTIVE_PARTNER_PROCESSED
        self.save()


class ProspectiveContact(models.Model):
    """
    A ProspectiveContact is a person's name and contact details, with a
    link to a Prospective Partner and a role within it.
    It does not have a corresponding User object.
    It is meant to be used internally at SciPost, during Partner mining.
    """
    prospartner = models.ForeignKey('partners.ProspectivePartner', on_delete=models.CASCADE,
                                    related_name='prospective_contacts')
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    role = models.CharField(max_length=128)

    def __str__(self):
        return "%s %s %s" % (self.get_title_display(), self.first_name, self.last_name)


class ProspectivePartnerEvent(models.Model):
    prospartner = models.ForeignKey('partners.ProspectivePartner', on_delete=models.CASCADE)
    event = models.CharField(max_length=64, choices=PROSPECTIVE_PARTNER_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey('scipost.Contributor',
                                 on_delete=models.SET(get_sentinel_user),
                                 blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.prospartner, self.get_event_display())


###########################
# Partner-related objects #
###########################

class Institution(models.Model):
    """
    An Institution is any form of academic organization which SciPost interacts with.
    """
    kind = models.CharField(max_length=32, choices=PARTNER_KINDS)
    name = models.CharField(max_length=256)
    logo = models.ImageField(upload_to='institutions/logo/%Y/', blank=True)
    css_class = models.CharField(max_length=256, blank=True,
                                 verbose_name="Additional logo CSS class")
    acronym = models.CharField(max_length=16)
    address = models.TextField(blank=True)
    country = CountryField()

    def __str__(self):
        return '%s (%s)' % (self.name, self.get_kind_display())


class ContactRequest(models.Model):
    """
    A ContactRequest request for a new Contact usually made by another Contact.
    The requests are saved to this separate model to also be able to request new
    Contact links if a Contact is already registered, but not linked to a specific Partner.
    """
    email = models.EmailField()
    kind = ChoiceArrayField(models.CharField(max_length=4, choices=CONTACT_TYPES))
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    description = models.CharField(max_length=256, blank=True)
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE)
    status = models.CharField(max_length=4, choices=REQUEST_STATUSES, default=REQUEST_INITIATED)

    objects = ContactRequestManager()

    def __str__(self):
        return '%s %s %s' % (self.get_title_display(), self.first_name, self.last_name)


class Contact(models.Model):
    """
    A Contact is a simple form of User which is meant
    to be associated to Partner objects
    (main contact, financial/technical contact etc).
    Contacts and Contributors have different rights.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True,
                                related_name='partner_contact')
    kind = ChoiceArrayField(models.CharField(max_length=4, choices=CONTACT_TYPES))
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    description = models.CharField(max_length=256, blank=True)
    partners = models.ManyToManyField('partners.Partner',
                                      help_text=('All Partners (+related Institutions)'
                                                 ' the Contact is related to.'))
    consortia = models.ManyToManyField('partners.Consortium', blank=True,
                                       help_text=('All Consortia for which the Contact has'
                                                  ' explicit permission to view/edit its data.'))
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return '%s %s, %s' % (self.get_title_display(), self.user.last_name, self.user.first_name)

    def generate_key(self, feed=''):
        """
        Generate and save a new activation_key for the Contact, given a certain feed.
        """
        for i in range(5):
            feed += random.choice(string.ascii_letters)
        feed = feed.encode('utf8')
        salt = self.user.username.encode('utf8')
        self.activation_key = hashlib.sha1(salt + feed).hexdigest()
        self.key_expires = now + datetime.timedelta(days=2)

    def save(self, *args, **kwargs):
        if not self.activation_key:
            self.generate_key()
        super().save(*args, **kwargs)

    def delete_or_remove_partner(self, partner, *args, **kwargs):
        """
        Custom `delete` method as the contact does not always need to be deleted,
        but sometimes just the link with a specific partner needs to be removed.
        """
        self.partners.remove(partner)
        if self.partners.exists():
            return self
        try:
            # User also has a Contributor-side, do not remove complete User
            self.user.contributor
            return super().delete(*args, **kwargs)
        except Contributor.DoesNotExist:
            # Remove User; casade-remove this Contact
            self.user.delete()
            return self

    @property
    def kind_display(self):
        """
        Due to a lack of support to use get_FOO_display in a ArrayField, one has to create
        one 'manually'.
        """
        choices = dict(CONTACT_TYPES)
        return ', '.join([choices[value] for index, value in enumerate(self.kind)])


class Partner(models.Model):
    """
    Supporting Partners.
    These are the official Partner objects created by SciPost Admin.
    """
    institution = models.ForeignKey('partners.Institution', on_delete=models.CASCADE,
                                    blank=True, null=True)
    status = models.CharField(max_length=16, choices=PARTNER_STATUS, default=PARTNER_INITIATED)
    main_contact = models.ForeignKey('partners.Contact', on_delete=models.SET_NULL,
                                     blank=True, null=True, related_name='partner_main_contact')

    objects = PartnerManager()

    def __str__(self):
        if self.institution:
            return self.institution.acronym + ' (' + self.get_status_display() + ')'
        return self.get_status_display()

    def get_absolute_url(self):
        return reverse('partners:partner_view', args=(self.id,))

    @property
    def has_all_contacts(self):
        """
        Determine if Partner has all available Contact Types available.
        """
        raise NotImplemented


class PartnerEvent(models.Model):
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE,
                                related_name='events')
    event = models.CharField(max_length=64, choices=PARTNER_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s' % (str(self.partner), self.get_event_display())


class Consortium(models.Model):
    """
    Collection of Partners.
    """
    name = models.CharField(max_length=128)
    partners = models.ManyToManyField('partners.Partner', blank=True)
    status = models.CharField(max_length=16, choices=CONSORTIUM_STATUS)

    class Meta:
        verbose_name_plural = 'consortia'


class MembershipAgreement(models.Model):
    """
    Agreement for membership of the Supporting Partners Board.
    A new instance is created each time an Agreement is made or renewed.
    """
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE,
                                blank=True, null=True, related_name='agreements')
    consortium = models.ForeignKey('partners.Consortium', on_delete=models.CASCADE,
                                   blank=True, null=True)
    status = models.CharField(max_length=16, choices=MEMBERSHIP_AGREEMENT_STATUS)
    date_requested = models.DateField()
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.DurationField(choices=MEMBERSHIP_DURATION)
    offered_yearly_contribution = models.SmallIntegerField(default=0, help_text="Yearly contribution in euro's (€)")

    objects = MembershipAgreementManager()

    def __str__(self):
        return (str(self.partner) +
                ' [' + self.get_duration_display() +
                ' from ' + self.start_date.strftime('%Y-%m-%d') + ']')

    def get_absolute_url(self):
        return reverse('partners:agreement_details', args=(self.id,))


class PartnersAttachment(models.Model):
    """
    An Attachment which can (in the future) be related to a Partner, Contact, MembershipAgreement,
    etc.
    """
    attachment = models.FileField(upload_to='UPLOADS/PARTNERS/ATTACHMENTS',
                                  storage=SecureFileStorage())
    name = models.CharField(max_length=128)
    agreement = models.ForeignKey('partners.MembershipAgreement', related_name='attachments',
                                  blank=True)

    objects = PartnersAttachmentManager()

    def get_absolute_url(self):
        if self.agreement:
            return reverse('partners:agreement_attachments', args=(self.agreement.id, self.id))
