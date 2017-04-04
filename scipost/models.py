import datetime

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.utils.safestring import mark_safe

from django_countries.fields import CountryField

from .behaviors import TimeStampedModel
from .constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS,\
                       subject_areas_dict, CONTRIBUTOR_STATUS, TITLE_CHOICES,\
                       INVITATION_STYLE, INVITATION_TYPE,\
                       INVITATION_CONTRIBUTOR, INVITATION_FORMAL,\
                       AUTHORSHIP_CLAIM_PENDING, AUTHORSHIP_CLAIM_STATUS,\
                       PARTNER_TYPES, PARTNER_STATUS,\
                       SPB_MEMBERSHIP_AGREEMENT_STATUS, SPB_MEMBERSHIP_DURATION
from .fields import ChoiceArrayField
from .managers import FellowManager


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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    invitation_key = models.CharField(max_length=40, default='',
                                      blank=True, null=True)
    activation_key = models.CharField(max_length=40, default='')
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

    def __str__(self):
        return '%s, %s' % (self.user.last_name, self.user.first_name)

    def get_title(self):
        # Please use get_title_display(). To be removed in future
        return self.get_title_display()

    def is_currently_available(self):
        unav_periods = UnavailabilityPeriod.objects.filter(contributor=self)

        today = datetime.date.today()
        for unav in unav_periods:
            if unav.start < today and unav.end > today:
                return False
        return True

    def private_info_as_table(self):
        template = Template('''
            <table>
            <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
            <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
            <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
            <tr><td>Email: </td><td>&nbsp;</td><td>{{ email }}</td></tr>
            <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
            <tr><td>Country of employment: </td><td>&nbsp;</td>
            <td>{{ country_of_employment }}</td></tr>
            <tr><td>Affiliation: </td><td>&nbsp;</td><td>{{ affiliation }}</td></tr>
            <tr><td>Address: </td><td>&nbsp;</td><td>{{ address }}</td></tr>
            <tr><td>Personal web page: </td><td>&nbsp;</td><td>{{ personalwebpage }}</td></tr>
            <tr><td>Accept SciPost emails: </td><td>&nbsp;</td><td>{{ accepts_SciPost_emails }}</td></tr>
            </table>
        ''')
        context = Context({
            'title': self.get_title_display(),
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'orcid_id': self.orcid_id,
            'country_of_employment': str(self.country_of_employment.name),
            'affiliation': self.affiliation,
            'address': self.address,
            'personalwebpage': self.personalwebpage,
            'accepts_SciPost_emails': self.accepts_SciPost_emails,
        })
        return template.render(context)

    def public_info_as_table(self):
        """Prints out all publicly-accessible info as a table."""

        template = Template('''
            <table>
            <tr><td>Title: </td><td>&nbsp;</td><td>{{ title }}</td></tr>
            <tr><td>First name: </td><td>&nbsp;</td><td>{{ first_name }}</td></tr>
            <tr><td>Last name: </td><td>&nbsp;</td><td>{{ last_name }}</td></tr>
            <tr><td>ORCID id: </td><td>&nbsp;</td><td>{{ orcid_id }}</td></tr>
            <tr><td>Country of employment: </td><td>&nbsp;</td>
            <td>{{ country_of_employment }}</td></tr>
            <tr><td>Affiliation: </td><td>&nbsp;</td><td>{{ affiliation }}</td></tr>
            <tr><td>Personal web page: </td><td>&nbsp;</td><td>{{ personalwebpage }}</td></tr>
            </table>
        ''')
        context = Context({
                'title': self.get_title_display(),
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'email': self.user.email,
                'orcid_id': self.orcid_id,
                'country_of_employment': str(self.country_of_employment.name),
                'affiliation': self.affiliation,
                'address': self.address,
                'personalwebpage': self.personalwebpage
                })
        return template.render(context)

    def discipline_as_string(self):
        # Redundant, to be removed in future
        return self.get_discipline_display()

    def expertises_as_ul(self):
        output = '<ul>'
        if self.expertises:
            for exp in self.expertises:
                output += '<li>%s</li>' % subject_areas_dict[exp]
        output += '</ul>'
        return mark_safe(output)

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
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email = models.EmailField()
    invitation_type = models.CharField(max_length=2, choices=INVITATION_TYPE,
                                       default=INVITATION_CONTRIBUTOR)
    cited_in_submission = models.ForeignKey('submissions.Submission',
                                            on_delete=models.CASCADE,
                                            blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    drafted_by = models.ForeignKey(Contributor,
                                   on_delete=models.CASCADE,
                                   blank=True, null=True)
    date_drafted = models.DateTimeField(default=timezone.now)
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
                                            blank=True, null=True)
    cited_in_publication = models.ForeignKey('journals.Publication',
                                             on_delete=models.CASCADE,
                                             blank=True, null=True)
    message_style = models.CharField(max_length=1, choices=INVITATION_STYLE,
                                     default=INVITATION_FORMAL)
    personal_message = models.TextField(blank=True, null=True)
    invitation_key = models.CharField(max_length=40, default='')
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
        return (self.invitation_type + ' ' + self.first_name + ' ' + self.last_name
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
            text += self.cited_in_submission.arxiv_nr_w_vn_nr
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


#############################
# Supporting Partners Board #
#############################

class SupportingPartner(models.Model):
    """
    Supporting Partners.
    """
    partner_type = models.CharField(max_length=32, choices=PARTNER_TYPES)
    status = models.CharField(max_length=16, choices=PARTNER_STATUS)
    institution = models.CharField(max_length=256)
    institution_acronym = models.CharField(max_length=10)
    institution_address = models.CharField(max_length=1000)
    consortium_members = models.TextField(blank=True, null=True)
    contact_person = models.ForeignKey(Contributor, on_delete=models.CASCADE)

    def __str__(self):
        return self.institution_acronym + ' (' + self.get_status_display() + ')'


class SPBMembershipAgreement(models.Model):
    """
    Agreement for membership of the Supporting Partners Board.
    A new instance is created each time an Agreement is made or renewed.
    """
    partner = models.ForeignKey(SupportingPartner, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, choices=SPB_MEMBERSHIP_AGREEMENT_STATUS)
    date_requested = models.DateField()
    start_date = models.DateField()
    duration = models.DurationField(choices=SPB_MEMBERSHIP_DURATION)
    offered_yearly_contribution = models.SmallIntegerField(default=0)

    def __str__(self):
        return (str(self.partner) +
                ' [' + self.get_duration_display() +
                ' from ' + self.start_date.strftime('%Y-%m-%d') + ']')


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
