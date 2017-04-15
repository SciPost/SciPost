import datetime

from django.utils import timezone
from django.db import models, transaction
from django.contrib.postgres.fields import JSONField
from django.urls import reverse

from .constants import ASSIGNMENT_REFUSAL_REASONS, ASSIGNMENT_NULLBOOL,\
                       SUBMISSION_TYPE, ED_COMM_CHOICES, REFEREE_QUALIFICATION, QUALITY_SPEC,\
                       RANKING_CHOICES, REPORT_REC, SUBMISSION_STATUS, STATUS_UNASSIGNED,\
                       REPORT_STATUSES, STATUS_UNVETTED, STATUS_RESUBMISSION_SCREENING,\
                       SUBMISSION_CYCLES, CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC
from .managers import SubmissionManager, EditorialAssignmentManager, EICRecommendationManager
from .utils import ShortSubmissionCycle, DirectRecommendationSubmissionCycle,\
                   GeneralSubmissionCycle

from scipost.behaviors import ArxivCallable
from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS
from journals.constants import SCIPOST_JOURNALS_SUBMIT, SCIPOST_JOURNALS_DOMAINS
from journals.models import Publication


###############
# Submissions:
###############
class Submission(ArxivCallable, models.Model):
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

    # Metadata
    metadata = JSONField(default={}, blank=True, null=True)
    submission_date = models.DateField(verbose_name='submission date', default=timezone.now)
    latest_activity = models.DateTimeField(default=timezone.now)

    objects = SubmissionManager()

    class Meta:
        permissions = (
            ('can_take_editorial_actions', 'Can take editorial actions'),
            )

    def __init__(self, *args, **kwargs):
        """
        Append the specific submission cycle to the instance to eventually handle the
        complete submission cycle outside the submission instance itself.
        """
        super().__init__(*args, **kwargs)
        if self.refereeing_cycle == CYCLE_SHORT:
            self.cycle = ShortSubmissionCycle(self)
        elif self.refereeing_cycle == CYCLE_DIRECT_REC:
            self.cycle = DirectRecommendationSubmissionCycle(self)
        else:
            self.cycle = GeneralSubmissionCycle(self)

    def __str__(self):
        header = (self.arxiv_identifier_w_vn_nr + ', '
                  + self.title[:30] + ' by ' + self.author_list[:30])
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version ' + str(self.arxiv_vn_nr) + ')'
        try:
            header += ' (published as ' + self.publication.citation() + ')'
        except Publication.DoesNotExist:
            pass
        return header

    def get_absolute_url(self):
        return reverse('submissions:submission', args=[self.arxiv_identifier_w_vn_nr])

    @property
    def reporting_deadline_has_passed(self):
        return timezone.now() > self.reporting_deadline

    @transaction.atomic
    def finish_submission(self):
        if self.is_resubmission:
            # If submissions is a resubmission, the submission needs to be prescreened
            # by the EIC to choose which of the available submission cycle to assign
            self.mark_other_versions_as_deprecated()
            self.copy_authors_from_previous_version()
            self.copy_EIC_from_previous_version()
            self.set_resubmission_defaults()
            self.update_status(STATUS_RESUBMISSION_SCREENING)
        else:
            self.authors.add(self.submitted_by)

        self.save()

    @classmethod
    def same_version_exists(self, identifier):
        return self.objects.filter(arxiv_identifier_w_vn_nr=identifier).exists()

    @classmethod
    def different_versions(self, identifier):
        return self.objects.filter(arxiv_identifier_wo_vn_nr=identifier).order_by('-arxiv_vn_nr')

    def make_assignment(self):
        assignment = EditorialAssignment(
            submission=self,
            to=self.editor_in_charge,
            accepted=True,
            date_created=timezone.now(),
            date_answered=timezone.now(),
        )
        assignment.save()

    def update_status(self, status_code):
        if status_code in SUBMISSION_STATUS:
            self.status = status_code
            self.save()

    def set_resubmission_defaults(self):
        self.open_for_reporting = True
        self.open_for_commenting = True
        if self.other_versions()[0].submitted_to_journal == 'SciPost Physics Lecture Notes':
            self.reporting_deadline = timezone.now() + datetime.timedelta(days=56)
        else:
            self.reporting_deadline = timezone.now() + datetime.timedelta(days=28)

    def copy_EIC_from_previous_version(self):
        last_version = self.other_versions()[0]
        self.editor_in_charge = last_version.editor_in_charge
        self.status = 'EICassigned'

    def copy_authors_from_previous_version(self):
        last_version = self.other_versions()[0]

        for author in last_version.authors.all():
            self.authors.add(author)
        for author in last_version.authors_claims.all():
            self.authors_claims.add(author)
        for author in last_version.authors_false_claims.all():
            self.authors_false_claims.add(author)

    def mark_other_versions_as_deprecated(self):
        for sub in self.other_versions():
            sub.is_current = False
            sub.open_for_reporting = False
            sub.status = 'resubmitted'
            sub.save()

    def other_versions(self):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=self.arxiv_identifier_wo_vn_nr
        ).exclude(pk=self.id).order_by('-arxiv_vn_nr')

    # Underneath: All very inefficient methods as they initiate a new query
    def count_accepted_invitations(self):
        return self.refereeinvitation_set.filter(accepted=True).count()

    def count_declined_invitations(self):
        return self.refereeinvitation_set.filter(accepted=False).count()

    def count_pending_invitations(self):
        return self.refereeinvitation_set.filter(accepted=None).count()

    def count_invited_reports(self):
        return self.reports.filter(status=1, invited=True).count()

    def count_contrib_reports(self):
        return self.reports.filter(status=1, invited=False).count()

    def count_obtained_reports(self):
        return self.reports.filter(status=1, invited__isnull=False).count()

    def count_refused_resports(self):
        return self.reports.filter(status__lte=-1).count()

    def count_awaiting_vetting(self):
        return self.reports.filter(status=0).count()


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
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    referee = models.ForeignKey('scipost.Contributor', related_name='referee', blank=True, null=True,
                                on_delete=models.CASCADE)
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


###########
# Reports:
###########

class Report(models.Model):
    """ Both types of reports, invited or contributed. """
    status = models.SmallIntegerField(choices=REPORT_STATUSES, default=STATUS_UNVETTED)
    submission = models.ForeignKey('submissions.Submission', related_name='reports',
                                   on_delete=models.CASCADE)
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
        verbose_name="Qualification to referee this: I am ")
    # Text-based reporting
    strengths = models.TextField()
    weaknesses = models.TextField()
    report = models.TextField()
    requested_changes = models.TextField(verbose_name="requested changes")
    # Qualities:
    validity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    significance = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    originality = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    clarity = models.PositiveSmallIntegerField(choices=RANKING_CHOICES, default=101)
    formatting = models.SmallIntegerField(choices=QUALITY_SPEC,
                                          verbose_name="Quality of paper formatting")
    grammar = models.SmallIntegerField(choices=QUALITY_SPEC,
                                       verbose_name="Quality of English grammar")
    #
    recommendation = models.SmallIntegerField(choices=REPORT_REC)
    remarks_for_editors = models.TextField(default='', blank=True,
                                           verbose_name='optional remarks for the Editors only')
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')

    def __str__(self):
        return (self.author.user.first_name + ' ' + self.author.user.last_name + ' on ' +
                self.submission.title[:50] + ' by ' + self.submission.author_list[:50])


##########################
# EditorialCommunication #
##########################

class EditorialCommunication(models.Model):
    """
    Each individual communication between Editor-in-charge
    to and from Referees and Authors becomes an instance of this class.
    """
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    referee = models.ForeignKey('scipost.Contributor', related_name='referee_in_correspondence',
                                blank=True, null=True, on_delete=models.CASCADE)
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

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
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
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
