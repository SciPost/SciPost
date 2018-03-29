__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import random
import string

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from .behaviors import TimeStampedModel, orcid_validator
from .constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS,\
                       subject_areas_dict, CONTRIBUTOR_STATUS, TITLE_CHOICES,\
                       INVITATION_STYLE, INVITATION_TYPE,\
                       INVITATION_CONTRIBUTOR, INVITATION_FORMAL,\
                       AUTHORSHIP_CLAIM_PENDING, AUTHORSHIP_CLAIM_STATUS,\
                       CONTRIBUTOR_NEWLY_REGISTERED
from .fields import ChoiceArrayField
from .managers import FellowManager, ContributorQuerySet,\
                      UnavailabilityPeriodManager, AuthorshipClaimQuerySet

today = timezone.now().date()


def get_sentinel_user():
    '''
    Temporary fix: eventually the 'to-be-removed-Contributor' should be
    status: "deactivated" and anonymized.
    Fallback user for models relying on Contributor that is being deleted.
    '''
    user, __ = get_user_model().objects.get_or_create(username='deleted')
    return Contributor.objects.get_or_create(status=-4, user=user)[0]


class Contributor(models.Model):
    """
    All *science* users of SciPost are Contributors.
    username, password, email, first_name and last_name are inherited from User.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, unique=True)
    invitation_key = models.CharField(max_length=40, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)
    status = models.SmallIntegerField(default=CONTRIBUTOR_NEWLY_REGISTERED,
                                      choices=CONTRIBUTOR_STATUS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default='physics', verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id",
                                blank=True, validators=[orcid_validator])
    address = models.CharField(max_length=1000, verbose_name="address",
                               blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page',
                                      blank=True)
    vetted_by = models.ForeignKey('self', on_delete=models.SET(get_sentinel_user),
                                  related_name="contrib_vetted_by",
                                  blank=True, null=True)
    accepts_SciPost_emails = models.BooleanField(
        default=True,
        verbose_name="I accept to receive SciPost emails")

    objects = ContributorQuerySet.as_manager()

    def __str__(self):
        return '%s, %s' % (self.user.last_name, self.user.first_name)

    def save(self, *args, **kwargs):
        if not self.activation_key:
            self.generate_key()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('scipost:contributor_info', args=(self.id,))

    @property
    def get_formal_display(self):
        return '%s %s %s' % (self.get_title_display(), self.user.first_name, self.user.last_name)

    @property
    def is_currently_available(self):
        return not self.unavailability_periods.today().exists()

    def is_EdCol_Admin(self):
        return (self.user.groups.filter(name='Editorial Administrators').exists()
                or self.user.is_superuser)

    def is_SP_Admin(self):
        return (self.user.groups.filter(name='SciPost Administrators').exists()
                or self.user.is_superuser)

    def is_MEC(self):
        return self.fellowships.active().exists() or self.user.is_superuser

    def is_VE(self):
        return (self.user.groups.filter(name='Vetting Editors').exists()
                or self.user.is_superuser)

    def generate_key(self, feed=''):
        """
        Generate and save a new activation_key for the contributor, given a certain feed.
        """
        for i in range(5):
            feed += random.choice(string.ascii_letters)
        feed = feed.encode('utf8')
        salt = self.user.username.encode('utf8')
        self.activation_key = hashlib.sha1(salt+salt).hexdigest()
        self.key_expires = datetime.datetime.now() + datetime.timedelta(days=2)

    def expertises_as_string(self):
        if self.expertises:
            return ', '.join([subject_areas_dict[exp].lower() for exp in self.expertises])
        return ''


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
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    feedback = models.ForeignKey('virtualmeetings.Feedback', on_delete=models.CASCADE,
                                 blank=True, null=True)
    nomination = models.ForeignKey('virtualmeetings.Nomination', on_delete=models.CASCADE,
                                   blank=True, null=True)
    motion = models.ForeignKey('virtualmeetings.Motion', on_delete=models.CASCADE,
                               blank=True, null=True)
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

    def __str__(self):
        return (self.contributor.user.first_name + ' '
                + self.contributor.user.last_name + ' on '
                + self.date.strftime("%Y-%m-%d"))


###############
# Invitations #
###############

class DraftInvitation(models.Model):
    """
    Draft of an invitation, filled in by an officer.
    """
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    invitation_type = models.CharField(max_length=2, choices=INVITATION_TYPE,
                                       default=INVITATION_CONTRIBUTOR)
    cited_in_submission = models.ForeignKey('submissions.Submission',
                                            on_delete=models.CASCADE,
                                            blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    drafted_by = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                   blank=True, null=True)
    date_drafted = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return (self.invitation_type + ' ' + self.first_name + ' ' + self.last_name)


class RegistrationInvitation(models.Model):
    """
    Deprecated: Use the `invitations` app
    """
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
    """
    Deprecated: Use the `invitations` app
    """
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
    publication = models.ForeignKey('journals.Publication',
                                    on_delete=models.CASCADE,
                                    blank=True, null=True)
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


######################
# Static info models #
######################

class EditorialCollege(models.Model):
    '''A SciPost Editorial College for a specific discipline.'''
    discipline = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.discipline


class EditorialCollegeFellowship(TimeStampedModel):
    """
    Editorial College Fellowship connecting Editorial College and Contributors,
    maybe with a limiting start/until date.
    """
    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                    related_name='+')
    college = models.ForeignKey('scipost.EditorialCollege', on_delete=models.CASCADE,
                                related_name='fellowships')
    affiliation = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    until_date = models.DateField(null=True, blank=True)

    objects = FellowManager()

    class Meta:
        unique_together = ('contributor', 'college', 'start_date', 'until_date')

    def __str__(self):
        return self.contributor.__str__()

    def is_active(self):
        if not self.start_date:
            if not self.until_date:
                return True
            return today <= self.until_date
        elif not self.until_date:
            return today >= self.start_date
        return today >= self.start_date and today <= self.until_date
