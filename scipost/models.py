import datetime
import hashlib
import random
import string

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.template import Template, Context
from django.utils import timezone

from django_countries.fields import CountryField

from .behaviors import TimeStampedModel
from .constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS,\
                       subject_areas_dict, CONTRIBUTOR_STATUS, TITLE_CHOICES,\
                       INVITATION_STYLE, INVITATION_TYPE,\
                       INVITATION_CONTRIBUTOR, INVITATION_FORMAL,\
                       AUTHORSHIP_CLAIM_PENDING, AUTHORSHIP_CLAIM_STATUS
from .fields import ChoiceArrayField
from .managers import FellowManager, ContributorManager


def get_sentinel_user():
    '''
    Temporary fix: eventually the 'to-be-removed-Contributor' should be
    status: "deactivated" and anonymized.
    Fallback user for models relying on Contributor that is being deleted.
    '''
    user, new = User.objects.get_or_create(username='deleted')
    return Contributor.objects.get_or_create(status=-4, user=user)[0]


class Contributor(models.Model):
    """
    All users of SciPost are Contributors.
    Permissions determine the sub-types.
    username, password, email, first_name and last_name are inherited from User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    invitation_key = models.CharField(max_length=40, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)
    status = models.SmallIntegerField(default=0, choices=CONTRIBUTOR_STATUS)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default='physics', verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    orcid_id = models.CharField(max_length=20, verbose_name="ORCID id",
                                blank=True)
    country_of_employment = CountryField()
    affiliation = models.CharField(max_length=300, verbose_name='affiliation')
    address = models.CharField(max_length=1000, verbose_name="address",
                               default='', blank=True)
    personalwebpage = models.URLField(verbose_name='personal web page',
                                      blank=True)
    vetted_by = models.ForeignKey('self', on_delete=models.SET(get_sentinel_user),
                                  related_name="contrib_vetted_by",
                                  blank=True, null=True)
    accepts_SciPost_emails = models.BooleanField(
        default=True,
        verbose_name="I accept to receive SciPost emails")

    objects = ContributorManager()

    def __str__(self):
        return '%s, %s' % (self.user.last_name, self.user.first_name)

    def get_formal_display(self):
        return '%s %s %s' % (self.get_title_display(), self.user.first_name, self.user.last_name)

    def get_title(self):
        # Please use get_title_display(). To be removed in future
        return self.get_title_display()

    def is_SP_Admin(self):
        return self.user.groups.filter(name='SciPost Administrators').exists()

    def is_MEC(self):
        return self.user.groups.filter(name='Editorial College').exists()

    def is_VE(self):
        return self.user.groups.filter(name='Vetting Editors').exists()

    def is_currently_available(self):
        unav_periods = UnavailabilityPeriod.objects.filter(contributor=self)

        today = datetime.date.today()
        for unav in unav_periods:
            if unav.start < today and unav.end > today:
                return False
        return True

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
        self.save()

    def discipline_as_string(self):
        # Redundant, to be removed in future
        return self.get_discipline_display()

    def expertises_as_string(self):
        if self.expertises:
            return ', '.join([subject_areas_dict[exp].lower() for exp in self.expertises])
        return ''

    def assignments_summary_as_td(self):
        assignments = self.editorialassignment_set.all()
        nr_ongoing = assignments.filter(accepted=True, completed=False).count()
        nr_last_12mo = assignments.filter(
            date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_accepted = assignments.filter(accepted=True).count()
        nr_accepted_last_12mo = assignments.filter(
            accepted=True, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_refused = assignments.filter(accepted=False).count()
        nr_refused_last_12mo = assignments.filter(
            accepted=False, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_ignored = assignments.filter(accepted=None).count()
        nr_ignored_last_12mo = assignments.filter(
            accepted=None, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()
        nr_completed = assignments.filter(completed=True).count()
        nr_completed_last_12mo = assignments.filter(
            completed=True, date_created__gt=timezone.now() - timezone.timedelta(days=365)).count()

        context = Context({
            'nr_ongoing': nr_ongoing,
            'nr_total': assignments.count(),
            'nr_last_12mo': nr_last_12mo,
            'nr_accepted': nr_accepted,
            'nr_accepted_last_12mo': nr_accepted_last_12mo,
            'nr_refused': nr_refused,
            'nr_refused_last_12mo': nr_refused_last_12mo,
            'nr_ignored': nr_ignored,
            'nr_ignored_last_12mo': nr_ignored_last_12mo,
            'nr_completed': nr_completed,
            'nr_completed_last_12mo': nr_completed_last_12mo,
        })
        output = '<td>'
        if self.expertises:
            for expertise in self.expertises:
                output += subject_areas_dict[expertise] + '<br/>'
        output += ('</td>'
                   '<td>{{ nr_ongoing }}</td>'
                   '<td>{{ nr_last_12mo }} / {{ nr_total }}</td>'
                   '<td>{{ nr_accepted_last_12mo }} / {{ nr_accepted }}</td>'
                   '<td>{{ nr_refused_last_12mo }} / {{ nr_refused }}</td>'
                   '<td>{{ nr_ignored_last_12mo }} / {{ nr_ignored }}</td>'
                   '<td>{{ nr_completed_last_12mo }} / {{ nr_completed }}</td>\n')
        template = Template(output)
        return template.render(context)


class UnavailabilityPeriod(models.Model):
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()


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
    date = models.DateTimeField()
    remark = models.TextField()

    def __str__(self):
        return (self.contributor.user.first_name + ' '
                + self.contributor.user.last_name + ' on '
                + self.date.strftime("%Y-%m-%d"))

    def as_li(self):
        output = '<li><em>{{ by }}</em><p>{{ remark }}</p>'
        context = Context({'by': str(self),
                           'remark': self.remark})
        template = Template(output)
        return template.render(context)


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
    Invitation to particular persons for registration
    """
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
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
    invited_by = models.ForeignKey(Contributor,
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    responded = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    def __str__(self):
        return (self.first_name + ' ' + self.last_name
                + ' on ' + self.date_sent.strftime("%Y-%m-%d"))


class CitationNotification(models.Model):
    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    cited_in_submission = models.ForeignKey('submissions.Submission',
                                            on_delete=models.CASCADE,
                                            blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        text = str(self.contributor) + ', cited in '
        if self.cited_in_submission:
            text += self.cited_in_submission.arxiv_identifier_w_vn_nr
        elif self.cited_in_publication:
            text += self.cited_in_publication.citation()
        if self.processed:
            text += ' (processed)'
        return text


class AuthorshipClaim(models.Model):
    claimant = models.ForeignKey(Contributor,
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
    vetted_by = models.ForeignKey(Contributor,
                                  on_delete=models.CASCADE,
                                  blank=True, null=True)
    status = models.SmallIntegerField(choices=AUTHORSHIP_CLAIM_STATUS,
                                      default=AUTHORSHIP_CLAIM_PENDING)


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


#######################
# Affiliation Objects #
#######################

class AffiliationObject(models.Model):
    country = CountryField()
    institution = models.CharField(max_length=128)
    subunit = models.CharField(max_length=128)



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
        today = datetime.date.today()
        if not self.start_date:
            if not self.until_date:
                return True
            return today <= self.until_date
        elif not self.until_date:
            return today >= self.start_date
        return today >= self.start_date and today <= self.until_date
