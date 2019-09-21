__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import feedparser
import uuid

from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property

from .behaviors import SubmissionRelatedObjectMixin
from .constants import (
    ASSIGNMENT_REFUSAL_REASONS, ASSIGNMENT_NULLBOOL, SUBMISSION_TYPE, STATUS_PREASSIGNED,
    ED_COMM_CHOICES, REFEREE_QUALIFICATION, QUALITY_SPEC, RANKING_CHOICES, STATUS_INVITED,
    SUBMISSION_STATUS, SUBMISSION_UNDER_CONSIDERATION,
    REPORT_STATUSES, STATUS_UNVETTED, STATUS_INCOMING, STATUS_EIC_ASSIGNED,
    SUBMISSION_CYCLES, CYCLE_DEFAULT, CYCLE_SHORT, DECISION_FIXED, ASSIGNMENT_STATUSES,
    CYCLE_DIRECT_REC, EVENT_GENERAL, EVENT_TYPES, EVENT_FOR_AUTHOR, EVENT_FOR_EIC, REPORT_TYPES,
    REPORT_NORMAL, STATUS_DRAFT, STATUS_VETTED, EIC_REC_STATUSES, VOTING_IN_PREP, STATUS_UNASSIGNED,
    STATUS_INCORRECT, STATUS_UNCLEAR, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC, DEPRECATED,
    STATUS_FAILED_PRESCREENING, STATUS_RESUBMITTED, STATUS_REJECTED, STATUS_WITHDRAWN, REPORT_REC,
    STATUS_PUBLISHED, STATUS_REPLACED, STATUS_ACCEPTED, STATUS_DEPRECATED, STATUS_COMPLETED,
    PLAGIARISM_STATUSES, STATUS_WAITING)
from .managers import (
    SubmissionQuerySet, EditorialAssignmentQuerySet, EICRecommendationQuerySet, ReportQuerySet,
    SubmissionEventQuerySet, RefereeInvitationQuerySet, EditorialCommunicationQueryset)
from .refereeing_cycles import ShortCycle, DirectCycle, RegularCycle

from comments.behaviors import validate_file_extension, validate_max_file_size
from comments.models import Comment
from scipost.behaviors import TimeStampedModel
from scipost.constants import TITLE_CHOICES
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS, SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor
from scipost.storage import SecureFileStorage
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from journals.models import Publication
from mails.utils import DirectMailUtil


class Submission(models.Model):
    """SciPost register of an preprint (ArXiv articles only for now).

    A Submission is a centralized information package used in the refereeing cycle of a preprint.
    It collects information about authors, referee reports, editorial recommendations,
    college decisions, etc. etc. After an 'acceptance editorial recommendation', the Publication
    will directly be related to the latest Submission in the thread.
    """

    preprint = models.OneToOneField('preprints.Preprint', on_delete=models.CASCADE,
                                    related_name='submission')

    author_comments = models.TextField(blank=True)
    author_list = models.CharField(max_length=10000, verbose_name="author list")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    domain = models.CharField(max_length=3, choices=SCIPOST_JOURNALS_DOMAINS)
    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True, null=True, verbose_name='approach(es) [optional]')
    editor_in_charge = models.ForeignKey('scipost.Contributor', related_name='EIC', blank=True,
                                         null=True, on_delete=models.CASCADE)

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

    # Submission status fields
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS, default=STATUS_INCOMING)
    is_current = models.BooleanField(default=True)
    visible_public = models.BooleanField("Is publicly visible", default=False)
    visible_pool = models.BooleanField("Is visible in the Pool", default=False)
    is_resubmission_of = models.ForeignKey('self', blank=True, null=True,
                                           on_delete=models.SET_NULL, related_name='successor')
    thread_hash = models.UUIDField(default=uuid.uuid4)
    _is_resubmission = models.BooleanField(default=False)
    refereeing_cycle = models.CharField(
        max_length=30, choices=SUBMISSION_CYCLES, default=CYCLE_DEFAULT, blank=True)

    fellows = models.ManyToManyField('colleges.Fellowship', blank=True,
                                     related_name='pool')

    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPE, blank=True)
    submitted_by = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                     related_name='submitted_submissions')
    voting_fellows = models.ManyToManyField('colleges.Fellowship', blank=True,
                                            related_name='voting_pool')

    submitted_to = models.ForeignKey('journals.Journal', on_delete=models.CASCADE)
    proceedings = models.ForeignKey('proceedings.Proceedings', null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='submissions',
                                    help_text=(
                                        'Don\'t find the Proceedings you are looking for? '
                                        'Ask the conference organizers to contact our admin '
                                        'at admin@scipost.org to set things up.'))
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

    # iThenticate and conflicts
    needs_conflicts_update = models.BooleanField(default=True)
    plagiarism_report = models.OneToOneField(
        'submissions.iThenticateReport', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='to_submission')

    # Arxiv identifiers with/without version number
    arxiv_identifier_w_vn_nr = models.CharField(max_length=15, default='0000.00000v0')
    arxiv_identifier_wo_vn_nr = models.CharField(max_length=10, default='0000.00000')
    arxiv_vn_nr = models.PositiveSmallIntegerField(default=1)
    arxiv_link = models.URLField(verbose_name='arXiv link (including version nr)')

    pdf_refereeing_pack = models.FileField(upload_to='UPLOADS/REFEREE/%Y/%m/',
                                           max_length=200, blank=True)

    # Metadata
    metadata = JSONField(default=dict, blank=True, null=True)
    submission_date = models.DateField(verbose_name='submission date', default=datetime.date.today)
    acceptance_date = models.DateField(verbose_name='acceptance date', null=True, blank=True)
    latest_activity = models.DateTimeField(auto_now=True)
    update_search_index = models.BooleanField(default=True)

    # Topics for semantic linking
    topics = models.ManyToManyField('ontology.Topic', blank=True)

    objects = SubmissionQuerySet.as_manager()

    # Temporary
    invitation_order = models.IntegerField(default=0)

    class Meta:
        app_label = 'submissions'

    def save(self, *args, **kwargs):
        """Prefill some fields before saving."""
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'cycle'):
            self.set_cycle()
        return obj

    def __str__(self):
        """Summerize the Submission in a string."""
        header = '{identifier}, {title} by {authors}'.format(
            identifier=self.preprint.identifier_w_vn_nr,
            title=self.title[:30],
            authors=self.author_list[:30])
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version ' + str(self.preprint.vn_nr) + ')'
        if hasattr(self, 'publication') and self.publication.is_published:
            header += ' (published as %s (%s))' % (
                self.publication.doi_string, self.publication.publication_date.strftime('%Y'))
        return header

    def touch(self):
        """Update latest activity timestamp."""
        Submission.objects.filter(id=self.id).update(latest_activity=timezone.now())

    def comments_set_complete(self):
        """Return Comments on Submissions, Reports and other Comments."""
        return Comment.objects.filter(
            Q(submissions=self) | Q(reports__submission=self) |
            Q(comments__reports__submission=self) | Q(comments__submissions=self)).distinct()

    @property
    def cycle(self):
        """Get cycle object that's relevant for the Submission."""
        if not hasattr(self, '_cycle'):
            self.set_cycle()
        return self._cycle

    def set_cycle(self):
        """Set cycle to the Submission on request."""
        if self.refereeing_cycle == CYCLE_SHORT:
            self._cycle = ShortCycle(self)
        elif self.refereeing_cycle == CYCLE_DIRECT_REC:
            self._cycle = DirectCycle(self)
        else:
            self._cycle = RegularCycle(self)

    def get_absolute_url(self):
        """Return url of the Submission detail page."""
        return reverse('submissions:submission', args=(self.preprint.identifier_w_vn_nr,))

    def get_notification_url(self, url_code):
        """Return url related to the Submission by the `url_code` meant for Notifications."""
        if url_code == 'editorial_page':
            return reverse('submissions:editorial_page', args=(self.preprint.identifier_w_vn_nr,))
        return self.get_absolute_url()

    @property
    def is_resubmission(self):
        return self.is_resubmission_of is not None

    @property
    def notification_name(self):
        """Return string representation of this Submission as shown in Notifications."""
        return self.preprint.identifier_w_vn_nr

    @property
    def eic_recommendation_required(self):
        """Return if Submission needs a EICRecommendation to be formulated."""
        return not self.eicrecommendations.active().exists()

    @property
    def revision_requested(self):
        """Check if Submission has fixed EICRecommendation asking for revision."""
        return self.eicrecommendations.fixed().asking_revision().exists()

    @property
    def under_consideration(self):
        """
        Check if the Submission is currently under consideration
        (in other words: is undergoing editorial processing).
        """
        return self.status in SUBMISSION_UNDER_CONSIDERATION

    @property
    def open_for_resubmission(self):
        """Check if Submission has fixed EICRecommendation asking for revision."""
        if self.status != STATUS_EIC_ASSIGNED:
            return False
        return self.eicrecommendations.fixed().asking_revision().exists()

    @property
    def reporting_deadline_has_passed(self):
        """Check if Submission has passed it's reporting deadline."""
        if self.status in [STATUS_INCOMING, STATUS_UNASSIGNED]:
            # These statuses do not have a deadline
            return False

        return timezone.now() > self.reporting_deadline

    @property
    def reporting_deadline_approaching(self):
        """Check if reporting deadline is within 7 days from now but not passed yet."""
        if self.status in [STATUS_INCOMING, STATUS_UNASSIGNED]:
            # These statuses do not have a deadline
            return False

        if self.reporting_deadline_has_passed:
            return False
        return timezone.now() > self.reporting_deadline - datetime.timedelta(days=7)

    @property
    def is_open_for_reporting(self):
        """Check if Submission is open for reporting and within deadlines."""
        return self.open_for_reporting and not self.reporting_deadline_has_passed

    @property
    def original_submission_date(self):
        """Return the submission_date of the first Submission in the thread."""
        return Submission.objects.filter(
            thread_hash=self.thread_hash, is_resubmission_of__isnull=True).first().submission_date

    @property
    def in_refereeing_phase(self):
        """Check if Submission is in active refereeing phase.

        This is not meant for functional logic, rather for explanatory functionality to the user.
        """
        if self.eicrecommendations.active().exists():
            # Editorial Recommendation is formulated!
            return False

        if self.refereeing_cycle == CYCLE_DIRECT_REC:
            # There's no refereeing in this cycle at all.
            return False

        if self.referee_invitations.in_process().exists():
            # Some unfinished invitations exist still.
            return True

        if self.referee_invitations.awaiting_response().exists():
            # Some invitations have been sent out without a response.
            return True

        # Maybe: Check for unvetted Reports?
        return self.status == STATUS_EIC_ASSIGNED and self.is_open_for_reporting

    @property
    def can_reset_reporting_deadline(self):
        """Check if reporting deadline is allowed to be reset."""
        blocked_statuses = [
            STATUS_FAILED_PRESCREENING, STATUS_RESUBMITTED, STATUS_ACCEPTED,
            STATUS_REJECTED, STATUS_WITHDRAWN, STATUS_PUBLISHED]
        if self.status in blocked_statuses:
            return False

        if self.refereeing_cycle == CYCLE_DIRECT_REC:
            # This cycle doesn't have a formal refereeing round.
            return False

        return self.editor_in_charge is not None

    @property
    def thread(self):
        """Return all (public) Submissions in the database in this ArXiv identifier series."""
        return Submission.objects.public().filter(thread_hash=self.thread_hash).order_by(
            '-submission_date', '-preprint__vn_nr')

    @cached_property
    def other_versions(self):
        """Return other Submissions in the database in this ArXiv identifier series."""
        return self.get_other_versions().order_by('-preprint__vn_nr')

    def get_other_versions(self):
        """Return queryset of other Submissions with this ArXiv identifier series."""
        return Submission.objects.filter(thread_hash=self.thread_hash).exclude(pk=self.id)

    def get_latest_version(self):
        """Return the latest known version in the thread of this Submission."""
        return self.thread.first()

    def add_general_event(self, message):
        """Generate message meant for EIC and authors."""
        event = SubmissionEvent(
            submission=self,
            event=EVENT_GENERAL,
            text=message,
        )
        event.save()

    def add_event_for_author(self, message):
        """Generate message meant for authors only."""
        event = SubmissionEvent(
            submission=self,
            event=EVENT_FOR_AUTHOR,
            text=message,
        )
        event.save()

    def add_event_for_eic(self, message):
        """Generate message meant for EIC and Editorial Administration only."""
        event = SubmissionEvent(
            submission=self,
            event=EVENT_FOR_EIC,
            text=message,
        )
        event.save()

    def flag_coauthorships_arxiv(self, fellows):
        """Identify coauthorships from arXiv, using author surname matching."""
        coauthorships = {}
        if self.metadata and 'entries' in self.metadata:
            author_last_names = []
            for author in self.metadata['entries'][0]['authors']:
                # Gather author data to do conflict-of-interest queries with
                author_last_names.append(author['name'].split()[-1])
            authors_last_names_str = '+OR+'.join(author_last_names)

            for fellow in fellows:
                # For each fellow found, so a query with the authors to check for conflicts
                search_query = 'au:({fellow}+AND+({authors}))'.format(
                    fellow=fellow.contributor.user.last_name,
                    authors=authors_last_names_str)
                queryurl = 'https://export.arxiv.org/api/query?search_query={sq}'.format(
                    sq=search_query)
                queryurl += '&sortBy=submittedDate&sortOrder=descending&max_results=5'
                queryurl = queryurl.replace(' ', '+')  # Fallback for some last names with spaces
                queryresults = feedparser.parse(queryurl)
                if queryresults.entries:
                    coauthorships[fellow.contributor.user.last_name] = queryresults.entries
        return coauthorships

    def is_sending_editorial_invitations(self):
        """Return whether editorial assignments are being send out."""
        if self.status != STATUS_UNASSIGNED:
            # Only if status is unassigned.
            return False

        return self.editorial_assignments.filter(status=STATUS_PREASSIGNED).exists()

    def has_inadequate_pool_composition(self):
        """
        Check whether the EIC actually in the pool of the Submission.

        (Could happen on resubmission or reassignment after wrong Journal selection)
        """
        if not self.editor_in_charge:
            # None assigned yet.
            return False

        pool_contributors_ids = Contributor.objects.filter(
            fellowships__pool=self).values_list('id', flat=True)
        return self.editor_in_charge.id not in pool_contributors_ids



class SubmissionEvent(SubmissionRelatedObjectMixin, TimeStampedModel):
    """Private message directly related to a Submission.

    The SubmissionEvent's goal is to act as a messaging model for the Submission cycle.
    Its main audience will be the author(s) and the Editor-in-charge of a Submission.

    Be aware that both the author and editor-in-charge will read the submission event.
    Make sure the right text is given to the appropriate event-type, to protect
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
        """Summerize the SubmissionEvent's meta information."""
        return '%s: %s' % (str(self.submission), self.get_event_display())


######################
# Editorial workflow #
######################

class EditorialAssignment(SubmissionRelatedObjectMixin, models.Model):
    """Unique Fellow assignment to a Submission as Editor-in-Charge.

    An EditorialAssignment could be an invitation to be the Editor-in-Charge for a Submission,
    containing either its acceptance or rejection, or it is an immediate accepted assignment. In
    addition is registers whether the Fellow's duties are fullfilled or still ongoing.
    """

    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    to = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)

    status = models.CharField(
        max_length=16, choices=ASSIGNMENT_STATUSES, default=STATUS_PREASSIGNED)
    refusal_reason = models.CharField(
        max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS, blank=True, null=True)
    invitation_order = models.PositiveSmallIntegerField(default=0)

    date_created = models.DateTimeField(default=timezone.now)
    date_invited = models.DateTimeField(blank=True, null=True)
    date_answered = models.DateTimeField(blank=True, null=True)

    objects = EditorialAssignmentQuerySet.as_manager()

    class Meta:
        default_related_name = 'editorial_assignments'
        ordering = ['-date_created']

    def __str__(self):
        """Summerize the EditorialAssignment's basic information."""
        return (self.to.user.first_name + ' ' + self.to.user.last_name + ' to become EIC of ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', requested on ' + self.date_created.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        """Return url of the assignment's processing page."""
        return reverse('submissions:assignment_request', args=(self.id,))

    @property
    def notification_name(self):
        """Return string representation of this EditorialAssigment as shown in Notifications."""
        return self.submission.preprint.identifier_w_vn_nr

    @property
    def preassigned(self):
        return self.status == STATUS_PREASSIGNED

    @property
    def invited(self):
        return self.status == STATUS_INVITED

    @property
    def replaced(self):
        return self.status == STATUS_REPLACED

    @property
    def accepted(self):
        return self.status == STATUS_ACCEPTED

    @property
    def deprecated(self):
        return self.status == STATUS_DEPRECATED

    @property
    def completed(self):
        return self.status == STATUS_COMPLETED

    def send_invitation(self):
        """Send invitation and update status."""
        if self.status != STATUS_PREASSIGNED:
            # Only send if status is appropriate to prevent double sending
            return False

        # Send mail
        mail_sender = DirectMailUtil(mail_code='eic/assignment_request', assignment=self)
        mail_sender.send_mail()

        EditorialAssignment.objects.filter(
            id=self.id).update(date_invited=timezone.now(), status=STATUS_INVITED)

        return True


class RefereeInvitation(SubmissionRelatedObjectMixin, models.Model):
    """Invitation to a scientist to referee a Submission.

    A RefereeInvitation will invite a Contributor or a non-registered scientist to send
    a Report for a specific Submission. It will register its response to the invitation and
    the current status its refereeing duty if the invitation has been accepted.
    """
    profile = models.ForeignKey('profiles.Profile', on_delete=models.SET_NULL,
                                blank=True, null=True)
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='referee_invitations')
    referee = models.ForeignKey('scipost.Contributor', related_name='referee_invitations',
                                blank=True, null=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email_address = models.EmailField()

    # if Contributor not found, person is invited to register
    invitation_key = models.CharField(max_length=40, blank=True)
    date_invited = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey('scipost.Contributor', related_name='referee_invited_by',
                                   blank=True, null=True, on_delete=models.CASCADE)
    auto_reminders_allowed = models.BooleanField(default=True)
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    accepted = models.NullBooleanField(choices=ASSIGNMENT_NULLBOOL, default=None)
    date_responded = models.DateTimeField(blank=True, null=True)
    refusal_reason = models.CharField(max_length=3, choices=ASSIGNMENT_REFUSAL_REASONS,
                                      blank=True, null=True)
    fulfilled = models.BooleanField(default=False)  # True if a Report has been submitted
    cancelled = models.BooleanField(default=False)  # True if EIC has deactivated invitation

    objects = RefereeInvitationQuerySet.as_manager()

    class Meta:
        ordering = ['cancelled', 'date_invited']

    def __str__(self):
        """Summerize the RefereeInvitation's basic information."""
        return (self.first_name + ' ' + self.last_name + ' to referee ' +
                self.submission.title[:30] + ' by ' + self.submission.author_list[:30] +
                ', invited on ' + self.date_invited.strftime('%Y-%m-%d'))

    def get_absolute_url(self):
        """Return url of the invitation's processing page."""
        return reverse('submissions:accept_or_decline_ref_invitations', args=(self.id,))

    @property
    def referee_str(self):
        """Return the most up-to-date name of the Referee."""
        if self.referee:
            return str(self.referee)
        return self.last_name + ', ' + self.first_name

    @property
    def notification_name(self):
        """Return string representation of this RefereeInvitation as shown in Notifications."""
        return self.submission.preprint.identifier_w_vn_nr

    @property
    def related_report(self):
        """Return the Report that's been created for this invitation."""
        return self.submission.reports.filter(author=self.referee).last()

    @property
    def needs_response(self):
        """Check if invitation has no response in more than three days."""
        if not self.cancelled and self.accepted is None:
            if self.date_last_reminded:
                # No reponse in over three days since last reminder
                return timezone.now() - self.date_last_reminded > datetime.timedelta(days=3)

            # No reponse in over three days since original invite
            return timezone.now() - self.date_invited > datetime.timedelta(days=3)

        return False

    @property
    def needs_fulfillment_reminder(self):
        """Check if isn't fullfilled but deadline is closing in."""
        if self.accepted and not self.cancelled and not self.fulfilled:
            # Refereeing deadline closing in/overdue, but invitation isn't fulfilled yet.
            return (self.submission.reporting_deadline - timezone.now()).days < 7
        return False

    @property
    def is_overdue(self):
        """Check if isn't fullfilled but deadline has expired."""
        if self.accepted and not self.cancelled and not self.fulfilled:
            # Refereeing deadline closing in/overdue, but invitation isn't fulfilled yet.
            return (self.submission.reporting_deadline - timezone.now()).days < 0
        return False

    @property
    def needs_attention(self):
        """Check if invitation needs attention by the editor."""
        return self.needs_response or self.needs_fulfillment_reminder

    @property
    def get_status_display(self):
        """Get status: a combination between different boolean fields."""
        if self.cancelled:
            return 'Cancelled'
        if self.fulfilled:
            return 'Fulfilled'
        if self.accepted is None:
            return 'Awaiting response'
        elif self.accepted:
            return 'Accepted'
        else:
            return 'Declined ({})'.format(self.get_refusal_reason_display())

    def reset_content(self):
        """Reset the invitation's information as a new invitation."""
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
    """Report on a Submission written by a Contributor.

    The refereeing Report has evaluation (text) fields for different categories. In general,
    the Report shall have all of these fields filled. In case the Contributor has already written
    a Report on a earlier version of the Submission, he will be able to write a 'follow-up report'.
    A follow-up report is a Report with only the general `report` evaluation field being required.
    """

    status = models.CharField(max_length=16, choices=REPORT_STATUSES, default=STATUS_UNVETTED)
    report_type = models.CharField(max_length=32, choices=REPORT_TYPES, default=REPORT_NORMAL)
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
    author = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                               related_name='reports')
    qualification = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=REFEREE_QUALIFICATION,
        verbose_name="Qualification to referee this: I am")

    # Text-based reporting
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    report = models.TextField(blank=True)
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

    recommendation = models.SmallIntegerField(null=True, blank=True, choices=REPORT_REC)
    remarks_for_editors = models.TextField(blank=True,
                                           verbose_name='optional remarks for the Editors only')
    needs_doi = models.NullBooleanField(default=None)
    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation('journals.GenericDOIDeposit',
                                        related_query_name='genericdoideposit')
    doi_label = models.CharField(max_length=200, blank=True)
    anonymous = models.BooleanField(default=True, verbose_name='Publish anonymously')
    pdf_report = models.FileField(upload_to='UPLOADS/REPORTS/%Y/%m/', max_length=200, blank=True)

    date_submitted = models.DateTimeField('date submitted')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # Attachment
    file_attachment = models.FileField(
        upload_to='uploads/reports/%Y/%m/%d/', blank=True,
        validators=[validate_file_extension, validate_max_file_size],
        storage=SecureFileStorage())

    objects = ReportQuerySet.as_manager()

    class Meta:
        unique_together = ('submission', 'report_nr')
        default_related_name = 'reports'
        ordering = ['-date_submitted']

    def __str__(self):
        """Summerize the RefereeInvitation's basic information."""
        return (self.author.user.first_name + ' ' + self.author.user.last_name + ' on ' +
                self.submission.title[:50] + ' by ' + self.submission.author_list[:50])

    def save(self, *args, **kwargs):
        """Update report number before saving on creation."""
        if not self.report_nr:
            new_report_nr = self.submission.reports.aggregate(
                models.Max('report_nr')).get('report_nr__max')
            if new_report_nr:
                new_report_nr += 1
            else:
                new_report_nr = 1
            self.report_nr = new_report_nr
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return url of the Report on the Submission detail page."""
        return self.submission.get_absolute_url() + '#report_' + str(self.report_nr)

    def get_notification_url(self, url_code):
        """Return url related to the Report by the `url_code` meant for Notifications."""
        if url_code == 'report_form':
            return reverse(
                'submissions:submit_report', args=(self.submission.preprint.identifier_w_vn_nr,))
        elif url_code == 'editorial_page':
            return reverse(
                'submissions:editorial_page', args=(self.submission.preprint.identifier_w_vn_nr,))
        return self.get_absolute_url()

    def get_attachment_url(self):
        """Return url of the Report its attachment if exists."""
        return reverse('submissions:report_attachment', kwargs={
            'identifier_w_vn_nr': self.submission.preprint.identifier_w_vn_nr,
            'report_nr': self.report_nr})

    @property
    def is_in_draft(self):
        """Return if Report is in draft."""
        return self.status == STATUS_DRAFT

    @property
    def is_vetted(self):
        """Return if Report is publicly available."""
        return self.status == STATUS_VETTED

    @property
    def is_unvetted(self):
        """Return if Report is awaiting vetting."""
        return self.status == STATUS_UNVETTED

    @property
    def is_rejected(self):
        """Return if Report is rejected."""
        return self.status in [
            STATUS_INCORRECT, STATUS_UNCLEAR, STATUS_NOT_USEFUL, STATUS_NOT_ACADEMIC]

    @property
    def notification_name(self):
        """Return string representation of this Report as shown in Notifications."""
        return self.submission.preprint.identifier_w_vn_nr

    @property
    def doi_string(self):
        """Return the doi with the registrant identifier prefix."""
        if self.doi_label:
            return '10.21468/' + self.doi_label
        return ''

    @cached_property
    def title(self):
        """Return the submission's title.

        This property is (mainly) used to let Comments get the title of the Submission without
        overcomplicated logic.
        """
        return self.submission.title

    @property
    def is_followup_report(self):
        """Return if Report is a follow-up Report instead of a regular Report.

        This property is used in the ReportForm, but will be candidate to become a database
        field if this information will become necessary in more general information representation.
        """
        return (self.author.reports.accepted().filter(
            submission__preprint__identifier_wo_vn_nr=self.submission.preprint.identifier_wo_vn_nr,
            submission__preprint__vn_nr__lt=self.submission.preprint.vn_nr).exists())

    @property
    def associated_published_doi(self):
        """Return the related Publication doi.

        Check if the Report relates to a SciPost-published object. If it is, return the doi
        of the published object.
        """
        try:
            publication = Publication.objects.get(
                accepted_submission__preprint__identifier_wo_vn_nr=self.submission.preprint.identifier_wo_vn_nr)
        except Publication.DoesNotExist:
            return None
        return publication.doi_string

    @property
    def relation_to_published(self):
        """Return dictionary with published object information.

        Check if the Report relates to a SciPost-published object. If it is, return a dict with
        info on relation to the published object, based on Crossref's peer review content type.
        """
        try:
            publication = Publication.objects.get(
                accepted_submission__preprint__identifier_wo_vn_nr=self.submission.preprint.identifier_wo_vn_nr)
        except Publication.DoesNotExist:
            return None

        relation = {
            'isReviewOfDOI': publication.doi_string,
            'stage': 'pre-publication',
            'type': 'referee-report',
            'title': 'Report on ' + self.submission.preprint.identifier_w_vn_nr,
            'contributor_role': 'reviewer',
        }
        return relation

    @property
    def citation(self):
        """Return the proper citation format for this Report."""
        citation = ''
        if self.doi_string:
            if self.anonymous:
                citation += 'Anonymous, '
            else:
                citation += '%s %s, ' % (self.author.user.first_name, self.author.user.last_name)
            citation += 'Report on arXiv:%s, ' % self.submission.preprint.identifier_w_vn_nr
            citation += 'delivered %s, ' % self.date_submitted.strftime('%Y-%m-%d')
            citation += 'doi: %s' % self.doi_string
        return citation

    def create_doi_label(self):
        """Create a doi in the default format."""
        Report.objects.filter(id=self.id).update(doi_label='SciPost.Report.{}'.format(self.id))

    def latest_report_from_thread(self):
        """Get latest Report of this Report's author for the Submission thread."""
        return self.author.reports.accepted().filter(
            submission__preprint__identifier_wo_vn_nr=self.submission.preprint.identifier_wo_vn_nr
        ).order_by('submission__preprint__identifier_wo_vn_nr').last()


##########################
# EditorialCommunication #
##########################

class EditorialCommunication(SubmissionRelatedObjectMixin, models.Model):
    """Message between two of the EIC, referees, Editorial Administration and/or authors."""

    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    referee = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                blank=True, null=True)
    comtype = models.CharField(max_length=4, choices=ED_COMM_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    text = models.TextField()

    objects = EditorialCommunicationQueryset.as_manager()

    class Meta:
        ordering = ['timestamp']
        default_related_name = 'editorial_communications'

    def __str__(self):
        """Summerize the EditorialCommunication's meta information."""
        output = self.comtype
        if self.referee is not None:
            output += ' ' + self.referee.user.first_name + ' ' + self.referee.user.last_name
        output += ' for submission {title} by {authors}'.format(
            title=self.submission.title[:30],
            authors=self.submission.author_list[:30])
        return output

    def get_absolute_url(self):
        """Return url of the related Submission detail page."""
        return self.submission.get_absolute_url()

    def get_notification_url(self, url_code):
        """Return url related to the Communication by the `url_code` meant for Notifications."""
        if url_code == 'editorial_page':
            return reverse(
                'submissions:editorial_page', args=(self.submission.preprint.identifier_w_vn_nr,))
        return self.get_absolute_url()


class EICRecommendation(SubmissionRelatedObjectMixin, models.Model):
    """
    The recommendation formulated for a specific Submission, formulated by the EIC.

    The EICRecommendation is the recommendation of a Submission written by the Editor-in-charge
    formulated at the end of the refereeing cycle. It can be voted for by a subset of Fellows and
    should contain the actual publication decision.
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
    status = models.CharField(max_length=32, choices=EIC_REC_STATUSES, default=VOTING_IN_PREP)
    version = models.SmallIntegerField(default=1)
    active = models.BooleanField(default=True)
    # status = models.CharField(default='', max_length=180)

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

    class Meta:
        unique_together = ('submission', 'version')
        ordering = ['version']

    def __str__(self):
        """Summerize the EICRecommendation's meta information."""
        return '{title} by {author}, {recommendation} version {version}'.format(
            title=self.submission.title[:20],
            author=self.submission.author_list[:30],
            recommendation=self.get_recommendation_display(),
            version=self.version,
        )

    def get_absolute_url(self):
        """Return url of the Submission detail page.

        Note that the EICRecommendation is not publicly visible, so the use of this url
        is limited.
        """
        return self.submission.get_absolute_url()

    @property
    def notification_name(self):
        """Return string representation of this EICRecommendation as shown in Notifications."""
        return self.submission.preprint.identifier_w_vn_nr

    @property
    def nr_for(self):
        """Return the number of votes 'for'."""
        return self.voted_for.count()

    @property
    def nr_against(self):
        """Return the number of votes 'against'."""
        return self.voted_against.count()

    @property
    def nr_abstained(self):
        """Return the number of votes 'abstained'."""
        return self.voted_abstain.count()

    @property
    def is_deprecated(self):
        """Check if Recommendation is deprecated."""
        return self.status == DEPRECATED

    @property
    def may_be_reformulated(self):
        """Check if this EICRecommdation is allowed to be reformulated in a new version."""
        if self.status == DEPRECATED:
            # Already reformulated before; please use the latest version
            return self.submission.eicrecommendations.last() == self
        return self.status != DECISION_FIXED

    def get_other_versions(self):
        """Return other versions of EICRecommendations for this Submission."""
        return self.submission.eicrecommendations.exclude(id=self.id)

    def get_full_status_display(self):
        """Return `status` field display plus possible `recommendation` display."""
        _str = self.get_status_display()
        if self.status == DECISION_FIXED and self.submission.status == STATUS_EIC_ASSIGNED:
            return '{} ({})'.format(_str, self.get_recommendation_display())
        return _str


class iThenticateReport(TimeStampedModel):
    """iThenticate report registration.

    iThenticateReport is the SciPost register of an iThenticate report saving basic information
    coming from iThenticate into the SciPost database for easy access.
    """

    uploaded_time = models.DateTimeField(null=True, blank=True)
    processed_time = models.DateTimeField(null=True, blank=True)
    doc_id = models.IntegerField(primary_key=True)
    part_id = models.IntegerField(null=True, blank=True)
    percent_match = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=PLAGIARISM_STATUSES, default=STATUS_WAITING)

    class Meta:
        verbose_name = 'iThenticate Report'
        verbose_name_plural = 'iThenticate Reports'

    def __str__(self):
        """Summerize the iThenticateReport's meta information."""
        _str = 'Report {doc_id}'.format(doc_id=self.doc_id)
        if hasattr(self, 'to_submission'):
            _str += ' on Submission {arxiv}'.format(
                arxiv=self.to_submission.preprint.identifier_w_vn_nr)
        return _str

    def save(self, *args, **kwargs):
        """Update the Submission's latest update timestamp on update."""
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'to_submission') and kwargs.get('commit', True):
            self.to_submission.touch()
        return obj

    def get_absolute_url(self):
        """Return url of the plagiarism detail page."""
        if hasattr(self, 'to_submission'):
            return reverse(
                'submissions:plagiarism',
                kwargs={'identifier_w_vn_nr': self.to_submission.preprint.identifier_w_vn_nr})
        return ''

    def get_report_url(self):
        """Request and return new read-only url from the iThenticate API.

        Note: The read-only link is valid for only 15 minutes, saving may be worthless
        """
        if not self.part_id:
            return ''

        from .plagiarism import iThenticate
        plagiarism = iThenticate()
        return plagiarism.get_url(self.part_id)

    @property
    def score(self):
        """Return the iThenticate score returned by their API as saved in the database."""
        return self.percent_match
