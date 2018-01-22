import datetime

from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property

from .behaviors import SubmissionRelatedObjectMixin
from .constants import ASSIGNMENT_REFUSAL_REASONS, ASSIGNMENT_NULLBOOL,\
                       SUBMISSION_TYPE, ED_COMM_CHOICES, REFEREE_QUALIFICATION, QUALITY_SPEC,\
                       RANKING_CHOICES, REPORT_REC, SUBMISSION_STATUS, STATUS_UNASSIGNED,\
                       REPORT_STATUSES, STATUS_UNVETTED, SUBMISSION_EIC_RECOMMENDATION_REQUIRED,\
                       SUBMISSION_CYCLES, CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC,\
                       EVENT_GENERAL, EVENT_TYPES, EVENT_FOR_AUTHOR, EVENT_FOR_EIC
from .managers import SubmissionQuerySet, EditorialAssignmentQuerySet, EICRecommendationQuerySet,\
                      ReportQuerySet, SubmissionEventQuerySet, RefereeInvitationQuerySet
from .utils import ShortSubmissionCycle, DirectRecommendationSubmissionCycle,\
                   GeneralSubmissionCycle

from comments.models import Comment
from scipost.behaviors import TimeStampedModel
from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from journals.constants import SCIPOST_JOURNALS_SUBMIT, SCIPOST_JOURNALS_DOMAINS
from journals.models import Publication


class Submission(models.Model):
    """
    Submission is a SciPost register of an ArXiv article. This object is the central
    instance for every action, recommendation, communication, etc. etc. that is related to the
    refereeing cycle of a Submission. A possible Publication object is later directly related
    to this Submission instance.
    """
    author_comments = models.TextField(blank=True)
    author_list = models.CharField(max_length=1000, verbose_name="author list")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    editor_in_charge = models.ForeignKey('scipost.Contributor', related_name='EIC', blank=True,
                                         null=True, on_delete=models.CASCADE)
    is_current = models.BooleanField(default=True)
    is_resubmission = models.BooleanField(default=False)
    list_of_changes = models.TextField(blank=True)
    open_for_commenting = models.BooleanField(default=False)
    open_for_reporting = models.BooleanField(default=False)
    referees_flagged = models.TextField(blank=True)
    referees_suggested = models.TextField(blank=True)
    remarks_for_editors = models.TextField(blank=True)
    reporting_deadline = models.DateTimeField(default=timezone.now)
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)

    # Refereeing fields
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS, default=STATUS_UNASSIGNED)
    refereeing_cycle = models.CharField(max_length=30, choices=SUBMISSION_CYCLES,
                                        default=CYCLE_DEFAULT)
    fellows = models.ManyToManyField('colleges.Fellowship', blank=True,
                                     related_name='pool')
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE,
                                       blank=True, null=True, default=None)
    submitted_by = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                     related_name='submitted_submissions')
    voting_fellows = models.ManyToManyField('colleges.Fellowship', blank=True,
                                            related_name='voting_pool')

    # Replace this by foreignkey?
    submitted_to_journal = models.CharField(max_length=30, choices=SCIPOST_JOURNALS_SUBMIT,
                                            verbose_name="Journal to be submitted to")
    proceedings = models.ForeignKey('proceedings.Proceedings', null=True, blank=True,
                                    related_name='submissions')
    title = models.CharField(max_length=300)

    # Authors which have been mapped to contributors:
    authors = models.ManyToManyField('scipost.Contributor', blank=True, related_name='submissions')
    authors_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                            related_name='claimed_submissions')
    authors_false_claims = models.ManyToManyField('scipost.Contributor', blank=True,
                                                  related_name='false_claimed_submissions')
    abstract = models.TextField()

    # Comments can be added to a Submission
    comments = GenericRelation('comments.Comment', related_query_name='submissions')

    # iThenticate Reports
    plagiarism_report = models.OneToOneField('submissions.iThenticateReport',
                                             on_delete=models.SET_NULL,
                                             null=True, blank=True,
                                             related_name='to_submission')

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

    objects = SubmissionQuerySet.as_manager()

    class Meta:
        app_label = 'submissions'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_cycle()

    def save(self, *args, **kwargs):
        # Fill `arxiv_identifier_w_vn_nr` as a dummy field for convenience
        arxiv_w_vn = '{arxiv}v{version}'.format(
            arxiv=self.arxiv_identifier_wo_vn_nr,
            version=self.arxiv_vn_nr)
        self.arxiv_identifier_w_vn_nr = arxiv_w_vn

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
            header += ' (published as %s (%s))' % (
                self.publication.doi_string, self.publication.publication_date.strftime('%Y'))
        except Publication.DoesNotExist:
            pass
        return header

    def touch(self):
        """ Update latest activity as a service """
        self.latest_activity = timezone.now()
        self.save()

    def comments_set_complete(self):
        """
        Return comments to Submission, comments on Reports of Submission and
        nested comments related to this Submission.
        """
        return Comment.objects.filter(Q(submissions=self) |
                                      Q(reports__submission=self) |
                                      Q(comments__reports__submission=self) |
                                      Q(comments__submissions=self)).distinct()

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

    @property
    def notification_name(self):
        return self.arxiv_identifier_w_vn_nr

    @property
    def eic_recommendation_required(self):
        return self.status in SUBMISSION_EIC_RECOMMENDATION_REQUIRED

    @property
    def reporting_deadline_has_passed(self):
        return timezone.now() > self.reporting_deadline

    @property
    def original_submission_date(self):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=self.arxiv_identifier_wo_vn_nr).first().submission_date

    @cached_property
    def other_versions(self):
        """
        Return all other versions of the Submission that are publicly accessible.
        """
        return Submission.objects.public().filter(
            arxiv_identifier_wo_vn_nr=self.arxiv_identifier_wo_vn_nr
        ).exclude(pk=self.id).order_by('-arxiv_vn_nr')

    @cached_property
    def other_versions_pool(self):
        """
        Return all other versions of the Submission.
        """
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


class SubmissionEvent(SubmissionRelatedObjectMixin, TimeStampedModel):
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

class EditorialAssignment(SubmissionRelatedObjectMixin, models.Model):
    """
    EditorialAssignment is a registration for Fellows of their duties of being a
    Editor-in-charge for a specific Submission. This model could start as a invitation only,
    which should then be accepted or declined by the invited.
    """
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

    objects = EditorialAssignmentQuerySet.as_manager()

    class Meta:
        default_related_name = 'editorial_assignments'
        ordering = ['-date_created']

    def __str__(self):
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', requested on ' + self.date_created.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        return reverse('submissions:assignment_request', args=(self.id,))

    @property
    def notification_name(self):
        return self.submission.arxiv_identifier_w_vn_nr


class RefereeInvitation(SubmissionRelatedObjectMixin, models.Model):
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='referee_invitations')
    referee = models.ForeignKey('scipost.Contributor', related_name='referee_invitations',
                                blank=True, null=True, on_delete=models.CASCADE)
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

    objects = RefereeInvitationQuerySet.as_manager()

    def __str__(self):
        return (self.first_name + ' ' + self.last_name + ' to referee ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', invited on ' + self.date_invited.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        return reverse('submissions:accept_or_decline_ref_invitations', args=(self.id,))

    @property
    def referee_str(self):
        if self.referee:
            return str(self.referee)
        return self.last_name + ', ' + self.first_name

    @property
    def notification_name(self):
        return self.submission.arxiv_identifier_w_vn_nr

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

class Report(SubmissionRelatedObjectMixin, models.Model):
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
    author = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                               related_name='reports')
    qualification = models.PositiveSmallIntegerField(
        choices=REFEREE_QUALIFICATION,
        verbose_name="Qualification to referee this: I am")

    # Text-based reporting
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    report = models.TextField()
    requested_changes = models.TextField(verbose_name="requested changes", blank=True)

    # Comments can be added to a Submission
    comments = GenericRelation('comments.Comment', related_query_name='reports')

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
    needs_doi = models.NullBooleanField(default=None)
    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation('journals.GenericDOIDeposit',
                                        related_query_name='genericdoideposit')
    doi_label = models.CharField(max_length=200, blank=True)
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')
    pdf_report = models.FileField(upload_to='UPLOADS/REPORTS/%Y/%m/', max_length=200, blank=True)

    objects = ReportQuerySet.as_manager()

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
    def notification_name(self):
        return self.submission.arxiv_identifier_w_vn_nr

    @property
    def doi_string(self):
        if self.doi_label:
            return '10.21468/' + self.doi_label
        return ''

    @cached_property
    def title(self):
        """
        This property is (mainly) used to let Comments get the title of the Submission without
        annoying logic.
        """
        return self.submission.title

    @property
    def is_followup_report(self):
        """
        Check if current Report is a `FollowupReport`. A Report is a `FollowupReport` if the
        author of the report already has a vetted report in the series of the specific Submission.
        """
        return (self.author.reports.accepted().filter(
            submission__arxiv_identifier_wo_vn_nr=self.submission.arxiv_identifier_wo_vn_nr,
            submission__arxiv_vn_nr__lt=self.submission.arxiv_vn_nr).exists())

    def save(self, *args, **kwargs):
        # Control Report count per Submission.
        if not self.report_nr:
            self.report_nr = self.submission.reports.count() + 1
        return super().save(*args, **kwargs)

    def create_doi_label(self):
        self.doi_label = 'SciPost.Report.' + str(self.id)
        self.save()

    def latest_report_from_series(self):
        """
        Get latest Report from the same author for the Submission series.
        """
        return (self.author.reports.accepted().filter(
            submission__arxiv_identifier_wo_vn_nr=self.submission.arxiv_identifier_wo_vn_nr)
                .order_by('submission__arxiv_identifier_wo_vn_nr').last())

    @property
    def relation_to_published(self):
        """
        Check if the Report relates to a SciPost-published object.
        If it is, return a dict with info on relation to the published object,
        based on Crossref's peer review content type.
        """
        publication = Publication.objects.get(
            accepted_submission__arxiv_identifier_wo_vn_nr=self.submission.arxiv_identifier_wo_vn_nr)
        if publication:
            relation = {
                'isReviewOfDOI': publication.doi_string,
                'stage': 'pre-publication',
                'type': 'referee-report',
                'title': 'Report on ' + self.submission.arxiv_identifier_w_vn_nr,
                'contributor_role': 'reviewer',
            }
            return relation

        return None

    @property
    def citation(self):
        citation = ''
        if self.doi_string:
            if self.anonymous:
                citation += 'Anonymous, '
            else:
                citation += '%s %s, ' % (self.author.user.first_name, self.author.user.last_name)
            citation += 'Report on %s, ' % self.submission.arxiv_identifier_w_vn_nr
            citation += 'doi: %s' % self.doi_string
        return citation


##########################
# EditorialCommunication #
##########################

class EditorialCommunication(SubmissionRelatedObjectMixin, models.Model):
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


class EICRecommendation(SubmissionRelatedObjectMixin, models.Model):
    """
    The EICRecommendation is the recommendation of a Submission written by
    the Editor-in-charge made at the end of the refereeing cycle. It can be voted for by
    a subset of Fellows and should contain the actual publication decision.
    """
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='eicrecommendations')
    date_submitted = models.DateTimeField('date submitted', default=timezone.now)
    remarks_for_authors = models.TextField(blank=True, null=True)
    requested_changes = models.TextField(verbose_name="requested changes", blank=True, null=True)
    remarks_for_editorial_college = models.TextField(blank=True,
                                                     verbose_name='optional remarks for the'
                                                                  ' Editorial College')
    recommendation = models.SmallIntegerField(choices=REPORT_REC)

    # Editorial Fellows who have assessed this recommendation:
    eligible_to_vote = models.ManyToManyField('scipost.Contributor', blank=True,
                                              related_name='eligible_to_vote')
    voted_for = models.ManyToManyField('scipost.Contributor', blank=True, related_name='voted_for')
    voted_against = models.ManyToManyField('scipost.Contributor', blank=True,
                                           related_name='voted_against')
    voted_abstain = models.ManyToManyField('scipost.Contributor', blank=True,
                                           related_name='voted_abstain')
    voting_deadline = models.DateTimeField('date submitted', default=timezone.now)

    objects = EICRecommendationQuerySet.as_manager()

    def __str__(self):
        return (self.submission.title[:20] + ' by ' + self.submission.author_list[:30] +
                ', ' + self.get_recommendation_display())

    def get_absolute_url(self):
        # TODO: Fix this weird redirect, but it's neccesary for the notifications to have one.
        return self.submission.get_absolute_url()

    @property
    def notification_name(self):
        return self.submission.arxiv_identifier_w_vn_nr

    @property
    def nr_for(self):
        return self.voted_for.count()

    @property
    def nr_against(self):
        return self.voted_against.count()

    @property
    def nr_abstained(self):
        return self.voted_abstain.count()


class iThenticateReport(TimeStampedModel):
    """
    iThenticateReport is the SciPost register of an iThenticate report. It saves
    basic information coming from iThenticate into the SciPost database for easy access.
    """
    uploaded_time = models.DateTimeField(null=True, blank=True)
    processed_time = models.DateTimeField(null=True, blank=True)
    doc_id = models.IntegerField(primary_key=True)
    part_id = models.IntegerField(null=True, blank=True)
    percent_match = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'iThenticate Report'
        verbose_name_plural = 'iThenticate Reports'

    def get_absolute_url(self):
        if hasattr(self, 'to_submission'):
            return reverse('submissions:plagiarism', kwargs={
                            'arxiv_identifier_w_vn_nr':
                            self.to_submission.arxiv_identifier_w_vn_nr})
        return None

    def get_report_url(self):
        """
        Request new read-only url from iThenticate and return.

        Note: The read-only link is valid for only 15 minutes, saving may be worthless
        """
        if not self.part_id:
            return ''

        from .plagiarism import iThenticate
        plagiarism = iThenticate()
        return plagiarism.get_url(self.part_id)

    def __str__(self):
        _str = 'Report {doc_id}'.format(doc_id=self.doc_id)
        if hasattr(self, 'to_submission'):
            _str += ' on Submission {arxiv}'.format(
                        arxiv=self.to_submission.arxiv_identifier_w_vn_nr)
        return _str

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'to_submission') and kwargs.get('commit', True):
            self.to_submission.touch()
        return obj

    @property
    def score(self):
        return self.percent_match
