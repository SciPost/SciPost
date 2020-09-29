__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import random
import string

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from .behaviors import TimeStampedModel, orcid_validator
from .constants import (
    SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS, subject_areas_dict, NORMAL_CONTRIBUTOR, DISABLED,
    TITLE_CHOICES, INVITATION_STYLE, INVITATION_TYPE, INVITATION_CONTRIBUTOR, INVITATION_FORMAL,
    AUTHORSHIP_CLAIM_PENDING, AUTHORSHIP_CLAIM_STATUS, CONTRIBUTOR_STATUSES, NEWLY_REGISTERED)
from .fields import ChoiceArrayField
from .managers import (
    FellowManager, ContributorQuerySet, UnavailabilityPeriodManager, AuthorshipClaimQuerySet)

from conflicts.models import ConflictOfInterest

today = timezone.now().date()


def get_sentinel_user():
    """Temporary fix to be able to delete Contributor instances.

    Eventually the 'to-be-removed-Contributor' should be status: "deactivated" and anonymized.
    Fallback user for models relying on Contributor that is being deleted.
    """
    user, __ = get_user_model().objects.get_or_create(username='deleted')
    return Contributor.objects.get_or_create(status=DISABLED, user=user)[0]


class TOTPDevice(models.Model):
    """
    Any device used by a User for 2-step authentication based on the RFC 6238 TOTP protocol.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    token = models.CharField(max_length=16)
    last_verified_counter = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        default_related_name = 'devices'
        verbose_name = 'TOTP Device'

    def __str__(self):
        return '{}: {}'.format(self.user, self.name)


class Contributor(models.Model):
    """A Contributor is an academic extention of the User model.

    All *science* users of SciPost are Contributors.
    username, password, email, first_name and last_name are inherited from User.
    """
    profile = models.OneToOneField('profiles.Profile', on_delete=models.SET_NULL,
                                   null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, unique=True)
    invitation_key = models.CharField(max_length=40, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=CONTRIBUTOR_STATUSES, default=NEWLY_REGISTERED)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id",
                                blank=True, validators=[orcid_validator])
    address = models.CharField(max_length=1000, verbose_name="address", blank=True)
    personalwebpage = models.URLField(max_length=300, verbose_name='personal web page', blank=True)
    vetted_by = models.ForeignKey('self', on_delete=models.SET(get_sentinel_user),
                                  related_name="contrib_vetted_by", blank=True, null=True)
    accepts_SciPost_emails = models.BooleanField(
        default=True, verbose_name="I accept to receive SciPost emails")
    # If this Contributor is merged into another, then this field is set to point to the new one:
    duplicate_of = models.ForeignKey('scipost.Contributor', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='duplicates')

    objects = ContributorQuerySet.as_manager()

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return '%s, %s' % (self.user.last_name, self.user.first_name)

    def save(self, *args, **kwargs):
        """Generate new activitation key if not set."""
        if not self.activation_key:
            self.generate_key()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return public information page url."""
        return reverse('scipost:contributor_info', args=(self.id,))

    @property
    def formal_str(self):
        return '%s %s' % (self.get_title_display(), self.user.last_name)

    @property
    def is_active(self):
        """
        Checks if the Contributor is registered, vetted,
        and has not been deactivated for any reason.
        """
        return self.user.is_active and self.status == NORMAL_CONTRIBUTOR

    @property
    def is_duplicate(self):
        return self.duplicate_of is not None

    @property
    def is_currently_available(self):
        """Check if Contributor is currently not marked as unavailable."""
        return not self.unavailability_periods.today().exists()

    def is_SP_Admin(self):
        """Check if Contributor is a SciPost Administrator."""
        return (self.user.groups.filter(name='SciPost Administrators').exists()
                or self.user.is_superuser)

    def is_Fin_Admin(self):
        """
        Check if Contributor is a SciPost Financial Administrator.
        """
        return (self.user.groups.filter(name='Financial Administrators').exists()
                or self.user.is_superuser)

    def is_EdCol_Admin(self):
        """Check if Contributor is an Editorial Administrator."""
        return (self.user.groups.filter(name='Editorial Administrators').exists()
                or self.user.is_superuser)

    def is_MEC(self):
        """Check if Contributor is a member of the Editorial College."""
        return self.fellowships.active().exists() or self.user.is_superuser

    def is_VE(self):
        """Check if Contributor is a Vetting Editor."""
        return (self.user.groups.filter(name='Vetting Editors').exists()
                or self.user.is_superuser)

    def generate_key(self, feed=''):
        """Generate a new activation_key for the contributor, given a certain feed."""
        for i in range(5):
            feed += random.choice(string.ascii_letters)
        feed = feed.encode('utf8')
        salt = self.user.username.encode('utf8')
        self.activation_key = hashlib.sha1(salt + feed).hexdigest()
        self.key_expires = timezone.now() + datetime.timedelta(days=2)

    def expertises_as_string(self):
        """Return joined expertises."""
        if self.expertises:
            return ', '.join([subject_areas_dict[exp].lower() for exp in self.expertises])
        return ''

    def conflict_of_interests(self):
        if not self.profile:
            return ConflictOfInterest.objects.none()
        return ConflictOfInterest.objects.filter_for_profile(self.profile)


class UnavailabilityPeriod(models.Model):
    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                    related_name='unavailability_periods')
    start = models.DateField()
    end = models.DateField()

    objects = UnavailabilityPeriodManager()

    class Meta:
        ordering = ['-start']

    def __str__(self):
        return '%s (%s to %s)' % (self.contributor, self.start, self.end)


class Remark(models.Model):
    """A form of non-public communication for VGMs and/or submissions and recommendations."""

    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    submission = models.ForeignKey('submissions.Submission',
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    recommendation = models.ForeignKey('submissions.EICRecommendation',
                                       on_delete=models.CASCADE,
                                       blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    remark = models.TextField()

    class Meta:
        default_related_name = 'remarks'
        ordering = ['date']

    def __str__(self):
        return (self.contributor.user.first_name + ' '
                + self.contributor.user.last_name + ' on '
                + self.date.strftime("%Y-%m-%d"))


###############
# Invitations #
###############

class RegistrationInvitation(models.Model):
    """Deprecated: Use the `invitations` app"""

    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    invitation_type = models.CharField(max_length=2, choices=INVITATION_TYPE,
                                       default=INVITATION_CONTRIBUTOR)
    cited_in_submission = models.ForeignKey('submissions.Submission',
                                            on_delete=models.CASCADE,
                                            blank=True, null=True,
                                            related_name='registration_invitations')
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    message_style = models.CharField(max_length=1, choices=INVITATION_STYLE,
                                     default=INVITATION_FORMAL)
    personal_message = models.TextField(blank=True)
    invitation_key = models.CharField(max_length=40, unique=True)
    key_expires = models.DateTimeField(default=timezone.now)
    date_sent = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey('scipost.Contributor',
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    responded = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    def __str__(self):
        return 'DEPRECATED'


class CitationNotification(models.Model):
    """Deprecated: Use the `invitations` app"""

    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
    cited_in_submission = models.ForeignKey('submissions.Submission',
                                            on_delete=models.CASCADE,
                                            blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    processed = models.BooleanField(default=False)


class AuthorshipClaim(models.Model):
    claimant = models.ForeignKey('scipost.Contributor',
                                 on_delete=models.CASCADE,
                                 related_name='claimant')
    submission = models.ForeignKey('submissions.Submission',
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    commentary = models.ForeignKey('commentaries.Commentary',
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    thesislink = models.ForeignKey('theses.ThesisLink',
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    vetted_by = models.ForeignKey('scipost.Contributor',
                                  on_delete=models.CASCADE,
                                  blank=True, null=True)
    status = models.SmallIntegerField(choices=AUTHORSHIP_CLAIM_STATUS,
                                      default=AUTHORSHIP_CLAIM_PENDING)

    objects = AuthorshipClaimQuerySet.as_manager()


class PrecookedEmail(models.Model):
    """
    Each instance contains an email template in both plain and html formats.
    Can only be created by Admins.
    For further use in scipost:send_precooked_email method.
    """
    email_subject = models.CharField(max_length=300)
    email_text = models.TextField()
    email_text_html = models.TextField()
    date_created = models.DateField(default=timezone.now)
    emailed_to = ArrayField(models.EmailField(blank=True), blank=True)
    date_last_used = models.DateField(default=timezone.now)
    deprecated = models.BooleanField(default=False)

    def __str__(self):
        return self.email_subject
