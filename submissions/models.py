import datetime

from django.utils import timezone
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.urls import reverse
from django.utils.functional import cached_property

from .constants import ASSIGNMENT_REFUSAL_REASONS, ASSIGNMENT_NULLBOOL,\
                       SUBMISSION_TYPE, ED_COMM_CHOICES, REFEREE_QUALIFICATION, QUALITY_SPEC,\
                       RANKING_CHOICES, REPORT_REC, SUBMISSION_STATUS, STATUS_UNASSIGNED,\
                       REPORT_STATUSES, STATUS_UNVETTED, SUBMISSION_EIC_RECOMMENDATION_REQUIRED,\
                       SUBMISSION_CYCLES, CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC,\
                       EVENT_GENERAL, EVENT_TYPES, EVENT_FOR_AUTHOR, EVENT_FOR_EIC
from .managers import SubmissionManager, EditorialAssignmentManager, EICRecommendationManager,\
                      ReportManager, SubmissionEventQuerySet
from .utils import ShortSubmissionCycle, DirectRecommendationSubmissionCycle,\
                   GeneralSubmissionCycle

from scipost.behaviors import TimeStampedModel
from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from journals.constants import SCIPOST_JOURNALS_SUBMIT, SCIPOST_JOURNALS_DOMAINS
from journals.models import Publication


###############
# Submissions:
###############
class Submission(models.Model):
    # Main submission fields
    author_comments = models.TextField(blank=True, null=True)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    editor_in_charge = models.ForeignKey('scipost.Contributor', related_name='EIC', blank=True,
                                         null=True, on_delete=models.CASCADE)
    is_current = models.BooleanField(default=True)
    is_resubmission = models.BooleanField(default=False)
    list_of_changes = models.TextField(blank=True, null=True)
    open_for_commenting = models.BooleanField(default=False)
    open_for_reporting = models.BooleanField(default=False)
    referees_flagged = models.TextField(blank=True, null=True)
    referees_suggested = models.TextField(blank=True, null=True)
    remarks_for_editors = models.TextField(blank=True, null=True)
    reporting_deadline = models.DateTimeField(default=timezone.now)
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    # Status set by Editors
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS, default=STATUS_UNASSIGNED)
    refereeing_cycle = models.CharField(max_length=30, choices=SUBMISSION_CYCLES,
                                        default=CYCLE_DEFAULT)
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE,
                                       blank=True, null=True, default=None)
    submitted_by = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
    # Replace this by foreignkey?
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT,
                                            verbose_name="Journal to be submitted to")
    title = models.CharField(max_length=300)

    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField('scipost.Contributor', blank=True, related_name='authors_sub')
    authors_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                            related_name='authors_sub_claims')
    authors_false_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                                  related_name='authors_sub_false_claims')
    abstract = models.TextField()

    # Arxiv identifiers with/without version number
    arxiv_identifier_w_vn_nr = models.CharField(max_length=15, default='0000.00000v0')
    arxiv_identifier_wo_vn_nr = models.CharField(max_length=10, default='0000.00000')
    arxiv_vn_nr = models.PositiveSmallIntegerField(default=1)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')

    pdf_refereeing_pack = models.FileField(upload_to='UPLOADS/REFEREE/%Y/%m/',
                                           max_length=200, blank=True)

    # Metadata
    metadata = JSONField(default={}, blank=True, null=True)
    submission_date = models.DateField(verbose_name='submission date', default=datetime.date.today)
    acceptance_date = models.DateField(verbose_name='acceptance date', null=True, blank=True)
    latest_activity = models.DateTimeField(auto_now=True)

    objects = SubmissionManager()

    class Meta:
        permissions = (
            ('can_take_editorial_actions', 'Can take editorial actions'),
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_cycle()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_cycle()

    def __str__(self):
        header = (self.arxiv_identifier_w_vn_nr + ', '
                  + self.title[:30] + ' by ' + self.author_list[:30])
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version ' + str(self.arxiv_vn_nr) + ')'
        try:
            header += ' (published as %s (%s))' % (self.publication.doi_string,
                                                   self.publication.publication_date.strftime('%Y'))
        except Publication.DoesNotExist:
            pass
        return header

    def _update_cycle(self):
        """
        Append the specific submission cycle to the instance to eventually handle the
        complete submission cycle outside the submission instance itself.
        """
        if self.refereeing_cycle == CYCLE_SHORT:
            self.cycle = ShortSubmissionCycle(self)
        elif self.refereeing_cycle == CYCLE_DIRECT_REC:
            self.cycle = DirectRecommendationSubmissionCycle(self)
        else:
            self.cycle = GeneralSubmissionCycle(self)

    def get_absolute_url(self):
        return reverse('submissions:submission', args=[self.arxiv_identifier_w_vn_nr])

    def eic_recommendation_required(self):
        return self.status not in SUBMISSION_EIC_RECOMMENDATION_REQUIRED

    @property
    def reporting_deadline_has_passed(self):
        return timezone.now() > self.reporting_deadline

    @cached_property
    def other_versions(self):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=self.arxiv_identifier_wo_vn_nr
        ).exclude(pk=self.id).order_by('-arxiv_vn_nr')

    # Underneath: All very inefficient methods as they initiate a new query
    def count_accepted_invitations(self):
        return self.referee_invitations.filter(accepted=True).count()

    def count_declined_invitations(self):
        return self.referee_invitations.filter(accepted=False).count()

    def count_pending_invitations(self):
        return self.referee_invitations.filter(accepted=None).count()

    def count_invited_reports(self):
        return self.reports.accepted().filter(invited=True).count()

    def count_contrib_reports(self):
        return self.reports.accepted().filter(invited=False).count()

    def count_obtained_reports(self):
        return self.reports.accepted().filter(invited__isnull=False).count()

    def add_general_event(self, message):
        event = SubmissionEvent(
            submission=self,
            event=EVENT_GENERAL,
            text=message,
        )
        event.save()

    def add_event_for_author(self, message):
        event = SubmissionEvent(
            submission=self,
            event=EVENT_FOR_AUTHOR,
            text=message,
        )
        event.save()

    def add_event_for_eic(self, message):
        event = SubmissionEvent(
            submission=self,
            event=EVENT_FOR_EIC,
            text=message,
        )
        event.save()


class SubmissionEvent(TimeStampedModel):
    """
    The SubmissionEvent's goal is to act as a messaging/logging model
    for the Submission cycle. Its main audience will be the author(s) and
    the Editor-in-charge of a Submission.

    Be aware!
    Both the author and editor-in-charge will read the submission event.
    Make sure the right text is given to the right event-type, to protect
    the fellow's identity.
    """
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='events')
    event = models.CharField(max_length=4, choices=EVENT_TYPES, default=EVENT_GENERAL)
    text = models.TextField()

    objects = SubmissionEventQuerySet.as_manager()

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return '%s: %s' % (str(self.submission), self.get_event_display())


######################
# Editorial workflow #
######################

class EditorialAssignment(models.Model):
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    to = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    # attribute `deprecated' becomes True if another Fellow becomes Editor-in-charge
    deprecated = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS,
                                      blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_answered = models.DateTimeField(blank=True, null=True)

    objects = EditorialAssignmentManager()

    def __str__(self):
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', requested on ' + self.date_created.strftime('%Y-%m-%d'))


class RefereeInvitation(models.Model):
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='referee_invitations')
    referee = models.ForeignKey('scipost.Contributor', related_name='referee', blank=True,
                                null=True, on_delete=models.CASCADE)  # Why is this blank/null=True
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    email_address = models.EmailField()
    # if Contributor not found, person is invited to register
    invitation_key = models.CharField(max_length=40, default='')
    date_invited = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey('scipost.Contributor', related_name='referee_invited_by',
                                   blank=True, null=True, on_delete=models.CASCADE)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    date_responded = models.DateTimeField(blank=True, null=True)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS,
                                      blank=True, null=True)
    fulfilled = models.BooleanField(default=False)  # True if a Report has been submitted
    cancelled = models.BooleanField(default=False)  # True if EIC has deactivated invitation

    def __str__(self):
        return (self.first_name + ' ' + self.last_name + ' to referee ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', invited on ' + self.date_invited.strftime('%Y-%m-%d'))

    @property
    def referee_str(self):
        if self.referee:
            return str(self.referee)
        return self.last_name + ', ' + self.first_name

    def reset_content(self):
        self.nr_reminders = 0
        self.date_last_reminded = None
        self.accepted = None
        self.refusal_reason = None
        self.fulfilled = False
        self.cancelled = False


###########
# Reports:
###########

class Report(models.Model):
    """
    Both types of reports, invited or contributed.

    This Report model acts as both a regular `Report` and a `FollowupReport`; A normal Report
    should have all fields required, whereas a FollowupReport only has the `report` field as
    a required field.

    Important note!
    Due to the construction of the two different types within a single model, it is important
    to explicitly implement the perticular differences in for example the form used.
    """
    status = models.CharField(max_length=16, choices=REPORT_STATUSES, default=STATUS_UNVETTED)
    submission = models.ForeignKey('submissions.Submission', related_name='reports',
                                   on_delete=models.CASCADE)
    report_nr = models.PositiveSmallIntegerField(default=0,
                                                 help_text='This number is a unique number '
                                                           'refeering to the Report nr. of '
                                                           'the Submission')
    vetted_by = models.ForeignKey('scipost.Contributor', related_name="report_vetted_by",
                                  blank=True, null=True, on_delete=models.CASCADE)

    # `invited' filled from RefereeInvitation objects at moment of report submission
    invited = models.BooleanField(default=False)

    # `flagged' if author of report has been flagged by submission authors (surname check only)
    flagged = models.BooleanField(default=False)
    date_submitted = models.DateTimeField('date submitted')
    author = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
    qualification = models.PositiveSmallIntegerField(
        choices=REFEREE_QUALIFICATION,
        verbose_name="Qualification to referee this: I am")

    # Text-based reporting
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    report = models.TextField()
    requested_changes = models.TextField(verbose_name="requested changes", blank=True)

    # Qualities:
    validity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES,
                                                null=True, blank=True)
    significance = models.PositiveSmallIntegerField(choices=RANKING_CHOICES,
                                                    null=True, blank=True)
    originality = models.PositiveSmallIntegerField(choices=RANKING_CHOICES,
                                                   null=True, blank=True)
    clarity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES,
                                               null=True, blank=True)
    formatting = models.SmallIntegerField(choices=QUALITY_SPEC, null=True, blank=True,
                                          verbose_name="Quality of paper formatting")
    grammar = models.SmallIntegerField(choices=QUALITY_SPEC, null=True, blank=True,
                                       verbose_name="Quality of English grammar")

    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    remarks_for_editors = models.TextField(blank=True,
                                           verbose_name='optional remarks for the Editors only')
    doi_label = models.CharField(max_length=200, blank=True)
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')
    pdf_report = models.FileField(upload_to='UPLOADS/REPORTS/%Y/%m/', max_length=200, blank=True)

    objects = ReportManager()

    class Meta:
        unique_together = ('submission', 'report_nr')
        default_related_name = 'reports'
        ordering = ['-date_submitted']

    def __str__(self):
        return (self.author.user.first_name + ' ' + self.author.user.last_name + ' on ' +
                self.submission.title[:50] + ' by ' + self.submission.author_list[:50])

    def get_absolute_url(self):
        return self.submission.get_absolute_url() + '#report_' + str(self.report_nr)

    @property
    def doi_string(self):
        if self.doi_label:
            return '10.21468/' + self.doi_label

    def save(self, *args, **kwargs):
        # Control Report count per Submission.
        if not self.report_nr:
            self.report_nr = self.submission.reports.count() + 1
        return super().save(*args, **kwargs)

    @cached_property
    def is_followup_report(self):
        """
        Check if current Report is a `FollowupReport`. A Report is a `FollowupReport` if the
        author of the report already has a vetted report in the series of the specific Submission.
        """
        return (self.author.reports.accepted()
                .filter(submission__arxiv_identifier_wo_vn_nr=self.submission.arxiv_identifier_wo_vn_nr)
                .exists())

    def latest_report_from_series(self):
        """
        Get latest Report from the same author for the Submission series.
        """
        return (self.author.reports.accepted()
                .filter(submission__arxiv_identifier_wo_vn_nr=self.submission.arxiv_identifier_wo_vn_nr)
                .order_by('submission__arxiv_identifier_wo_vn_nr').last())


##########################
# EditorialCommunication #
##########################

class EditorialCommunication(models.Model):
    """
    Each individual communication between Editor-in-charge
    to and from Referees and Authors becomes an instance of this class.
    """
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='editorial_communications')
    referee = models.ForeignKey('scipost.Contributor', related_name='referee_in_correspondence',
                                blank=True, null=True, on_delete=models.CASCADE)
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        output = self.comtype
        if self.referee is not None:
            output += ' ' + self.referee.user.first_name + ' ' + self.referee.user.last_name
        output += (' for submission ' + self.submission.title[:30] + ' by '
                   + self.submission.author_list[:30])
        return output


############################
# Editorial Recommendation #
############################

# From the Editor-in-charge of a Submission
class EICRecommendation(models.Model):
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='eicrecommendations')
    date_submitted = models.DateTimeField('date submitted', default=timezone.now)
    remarks_for_authors = models.TextField(blank=True, null=True)
    requested_changes = models.TextField(verbose_name="requested changes", blank=True, null=True)
    remarks_for_editorial_college = models.TextField(
        default='', blank=True, null=True,
        verbose_name='optional remarks for the Editorial College')
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    # Editorial Fellows who have assessed this recommendation:
    eligible_to_vote = models.ManyToManyField(Contributor, blank=True,
                                              related_name='eligible_to_vote')
    voted_for = models.ManyToManyField(Contributor, blank=True, related_name='voted_for')
    voted_against = models.ManyToManyField(Contributor, blank=True, related_name='voted_against')
    voted_abstain = models.ManyToManyField(Contributor, blank=True, related_name='voted_abstain')
    voting_deadline = models.DateTimeField('date submitted', default=timezone.now)

    objects = EICRecommendationManager()

    def __str__(self):
        return (self.submission.title[:20] + ' by ' + self.submission.author_list[:30] +
                ', ' + self.get_recommendation_display())

    @property
    def nr_for(self):
        return self.voted_for.count()

    @property
    def nr_against(self):
        return self.voted_against.count()

    @property
    def nr_abstained(self):
        return self.voted_abstain.count()
