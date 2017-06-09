from django.contrib.auth.models import User
from django.db import models

from django_countries.fields import CountryField

from .constants import PARTNER_KINDS, PARTNER_STATUS, CONSORTIUM_STATUS, MEMBERSHIP_DURATION,\
                       PROSPECTIVE_PARTNER_STATUS, PROSPECTIVE_PARTNER_EVENTS, PARTNER_EVENTS,\
                       MEMBERSHIP_AGREEMENT_STATUS, PROSPECTIVE_PARTNER_ADDED,\
                       PARTNER_KIND_UNI_LIBRARY
from .constants import PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT,\
                       PROSPECTIVE_PARTNER_APPROACHED,\
                       PROSPECTIVE_PARTNER_EVENT_INITIATE_NEGOTIATION,\
                       PROSPECTIVE_PARTNER_NEGOTIATING,\
                       PROSPECTIVE_PARTNER_EVENT_MARKED_AS_UNINTERESTED,\
                       PROSPECTIVE_PARTNER_UNINTERESTED,\
                       PROSPECTIVE_PARTNER_EVENT_PROMOTED,\
                       PROSPECTIVE_PARTNER_PROCESSED

from .managers import MembershipAgreementManager

from scipost.constants import TITLE_CHOICES
from scipost.models import get_sentinel_user


########################
# Prospective Partners #
########################

class ProspectivePartner(models.Model):
    """
    Created from the membership_request page, after submitting a query form.
    """
    kind = models.CharField(max_length=32, choices=PARTNER_KINDS, default=PARTNER_KIND_UNI_LIBRARY)
    institution_name = models.CharField(max_length=256)
    country = CountryField()
    date_received = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=32, choices=PROSPECTIVE_PARTNER_STATUS,
                              default=PROSPECTIVE_PARTNER_ADDED)

    def __str__(self):
        return '%s (received %s), %s' % (self.institution_name,
                                         self.date_received.strftime("%Y-%m-%d"),
                                         self.get_status_display())

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
    prospartner = models.ForeignKey('partners.ProspectivePartner', on_delete=models.CASCADE)
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
        return '%s: %s' % (str(self.prospective_partner), self.get_event_display())


###########################
# Partner-related objects #
###########################

class Institution(models.Model):
    """
    An Institution is any form of academic organization which SciPost interacts with.
    """
    kind = models.CharField(max_length=32, choices=PARTNER_KINDS)
    name = models.CharField(max_length=256)
    acronym = models.CharField(max_length=16)
    address = models.CharField(max_length=1000, blank=True)
    country = CountryField()

    def __str__(self):
        return '%s (%s)' % (self.name, self.get_kind_display())


class Contact(models.Model):
    """
    A Contact is a simple form of User which is meant
    to be associated to Partner objects
    (main contact, financial/technical contact etc).
    Contacts and Contributors have different rights.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    kind = models.CharField(max_length=128)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)

    def __str__(self):
        return '%s %s, %s' % (self.get_title_display(), self.user.last_name, self.user.first_name)


class Partner(models.Model):
    """
    Supporting Partners.
    These are the official Partner objects created by SciPost Admin.
    """
    institution = models.ForeignKey('partners.Institution', on_delete=models.CASCADE,
                                    blank=True, null=True)
    status = models.CharField(max_length=16, choices=PARTNER_STATUS)
    main_contact = models.ForeignKey('partners.Contact', on_delete=models.CASCADE,
                                     blank=True, null=True,
                                     related_name='partner_main_contact')
    financial_contact = models.ForeignKey('partners.Contact', on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          related_name='partner_financial_contact')
    technical_contact = models.ForeignKey('partners.Contact', on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          related_name='partner_technical_contact')

    def __str__(self):
        if self.institution:
            return self.institution.acronym + ' (' + self.get_status_display() + ')'
        return self.get_status_display()


class PartnerEvent(models.Model):
    partner = models.ForeignKey('partners.Partner', on_delete=models.CASCADE)
    event = models.CharField(max_length=64, choices=PARTNER_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)

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
                                blank=True, null=True)
    consortium = models.ForeignKey('partners.Consortium', on_delete=models.CASCADE,
                                   blank=True, null=True)
    status = models.CharField(max_length=16, choices=MEMBERSHIP_AGREEMENT_STATUS)
    date_requested = models.DateField()
    start_date = models.DateField()
    duration = models.DurationField(choices=MEMBERSHIP_DURATION)
    offered_yearly_contribution = models.SmallIntegerField(default=0)

    objects = MembershipAgreementManager()

    def __str__(self):
        return (str(self.partner) +
                ' [' + self.get_duration_display() +
                ' from ' + self.start_date.strftime('%Y-%m-%d') + ']')
