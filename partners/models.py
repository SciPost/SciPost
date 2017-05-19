from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from django_countries.fields import CountryField

from .constants import PARTNER_TYPES, PARTNER_STATUS, CONSORTIUM_STATUS,\
    MEMBERSHIP_AGREEMENT_STATUS, MEMBERSHIP_DURATION

from scipost.constants import TITLE_CHOICES
from scipost.models import Contributor


class ContactPerson(models.Model):
    """
    A ContactPerson is a simple form of User which is meant
    to be associated to Partner objects
    (main contact, financial/technical contact etc).
    ContactPersons and Contributors have different rights.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)

    def __str__(self):
        return '%s %s, %s' % (self.get_title_display(), self.user.last_name, self.user.first_name)


class Partner(models.Model):
    """
    Supporting Partners.
    These are the official Partner objects created by SciPost Admin.
    """
    partner_type = models.CharField(max_length=32, choices=PARTNER_TYPES)
    status = models.CharField(max_length=16, choices=PARTNER_STATUS)
    institution_name = models.CharField(max_length=256)
    institution_acronym = models.CharField(max_length=10)
    institution_address = models.CharField(max_length=1000, blank=True, null=True)
    country = CountryField()
    main_contact = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                     blank=True, null=True,
                                     related_name='partner_main_contact')
    financial_contact = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          related_name='partner_financial_contact')
    technical_contact = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                          blank=True, null=True,
                                          related_name='partner_technical_contact')

    def __str__(self):
        return self.institution_acronym + ' (' + self.get_status_display() + ')'


class Consortium(models.Model):
    """
    Collection of Partners.
    """
    name = models.CharField(max_length=128)
    partners = models.ManyToManyField(Partner, blank=True)
    status = models.CharField(max_length=16, choices=CONSORTIUM_STATUS)

    class Meta:
        verbose_name_plural = 'consortia'



class ProspectivePartner(models.Model):
    """
    Created from the membership_request page, after submitting a query form.
    """
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    email = models.EmailField()
    role = models.CharField(max_length=128)
    partner_type = models.CharField(max_length=32, choices=PARTNER_TYPES)
    institution_name = models.CharField(max_length=256)
    country = CountryField()
    date_received = models.DateTimeField(default=timezone.now)
    date_processed = models.DateTimeField(blank=True, null=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        resp = "processed"
        if not self.processed:
            resp = "unprocessed"
        return '%s (received %s), %s' % (self.institution_name,
                                         self.date_received.strftime("%Y-%m-%d"),
                                         resp)


class MembershipAgreement(models.Model):
    """
    Agreement for membership of the Supporting Partners Board.
    A new instance is created each time an Agreement is made or renewed.
    """
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True)
    consortium = models.ForeignKey(Consortium, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(max_length=16, choices=MEMBERSHIP_AGREEMENT_STATUS)
    date_requested = models.DateField()
    start_date = models.DateField()
    duration = models.DurationField(choices=MEMBERSHIP_DURATION)
    offered_yearly_contribution = models.SmallIntegerField(default=0)

    def __str__(self):
        return (str(self.partner) +
                ' [' + self.get_duration_display() +
                ' from ' + self.start_date.strftime('%Y-%m-%d') + ']')
