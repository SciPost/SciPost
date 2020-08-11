__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import feedparser
import uuid

from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from scipost.behaviors import TimeStampedModel
from scipost.constants import SCIPOST_DISCIPLINES, SCIPOST_SUBJECT_AREAS, SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor

from comments.models import Comment

from ..behaviors import SubmissionRelatedObjectMixin
from ..constants import (
    SUBMISSION_STATUS, STATUS_INCOMING, STATUS_UNASSIGNED, STATUS_PREASSIGNED,
    STATUS_EIC_ASSIGNED, SUBMISSION_UNDER_CONSIDERATION,
    STATUS_FAILED_PRESCREENING, STATUS_RESUBMITTED, STATUS_ACCEPTED,
    STATUS_REJECTED, STATUS_WITHDRAWN, STATUS_PUBLISHED,
    SUBMISSION_CYCLES, CYCLE_DEFAULT, CYCLE_SHORT, CYCLE_DIRECT_REC,
    EVENT_TYPES, EVENT_GENERAL, EVENT_FOR_AUTHOR, EVENT_FOR_EIC,
    SUBMISSION_TIERS)
from ..managers import SubmissionQuerySet, SubmissionEventQuerySet
from ..refereeing_cycles import ShortCycle, DirectCycle, RegularCycle


class Submission(models.Model):
    """
    A Submission is a preprint sent to SciPost for consideration.
    """

    preprint = models.OneToOneField('preprints.Preprint', on_delete=models.CASCADE,
                                    related_name='submission')

    author_comments = models.TextField(blank=True)
    author_list = models.CharField(max_length=10000, verbose_name="author list")
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES, default='physics')
    subject_area = models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS,
                                    verbose_name='Primary subject area', default='Phys:QP')
    secondary_areas = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
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

    # Submission status fields
    status = models.CharField(max_length=30, choices=SUBMISSION_STATUS, default=STATUS_INCOMING)
    is_current = models.BooleanField(default=True)
    visible_public = models.BooleanField("Is publicly visible", default=False)
    visible_pool = models.BooleanField("Is visible in the Pool", default=False)
    is_resubmission_of = models.ForeignKey('self', blank=True, null=True,
                                           on_delete=models.SET_NULL, related_name='successor')
    thread_hash = models.UUIDField(default=uuid.uuid4)
    refereeing_cycle = models.CharField(
        max_length=30, choices=SUBMISSION_CYCLES, default=CYCLE_DEFAULT, blank=True)

    fellows = models.ManyToManyField('colleges.Fellowship', blank=True,
                                     related_name='pool')

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

    # Links to associated code and data
    code_repository_url = models.URLField(
        blank=True,
        help_text='Link to a code repository pertaining to your manuscript'
    )
    data_repository_url = models.URLField(
        blank=True,
        help_text='Link to a data repository pertaining to your manuscript'
    )

    # Comments can be added to a Submission
    comments = GenericRelation('comments.Comment', related_query_name='submissions')

    # iThenticate and conflicts
    needs_conflicts_update = models.BooleanField(default=True)
    plagiarism_report = models.OneToOneField(
        'submissions.iThenticateReport', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='to_submission')

    pdf_refereeing_pack = models.FileField(upload_to='UPLOADS/REFEREE/%Y/%m/',
                                           max_length=200, blank=True)

    # Metadata
    metadata = JSONField(default=dict, blank=True, null=True)
    submission_date = models.DateTimeField(
        verbose_name='submission date',
        default=timezone.now)
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
        """Summarize the Submission in a string."""
        header = '{identifier}, {title} by {authors}'.format(
            identifier=self.preprint.identifier_w_vn_nr,
            title=self.title[:30],
            authors=self.author_list[:30])
        if self.is_current:
            header += ' (current version)'
        else:
            header += ' (deprecated version ' + str(self.thread_sequence_order) + ')'
        if hasattr(self, 'publication') and self.publication.is_published:
            header += ' (published as %s (%s))' % (
                self.publication.doi_string, self.publication.publication_date.strftime('%Y'))
        return header

    @property
    def authors_as_list(self):
        """Returns a python list of the authors, extracted from author_list field."""
        # Start by separating in comma's
        comma_separated = self.author_list.split(',')
        authors_as_list = []
        for entry in comma_separated:
            and_separated = entry.split(' and ')
            for subentry in and_separated:
                authors_as_list.append(subentry.lstrip().rstrip())
        return authors_as_list

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
        """Get cycle object relevant for the Submission."""
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
        """Return if Submission requires a EICRecommendation to be formulated."""
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
        """Check if Submission has passed its reporting deadline."""
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
        """Return all (public) Submissions in the database in this thread."""
        return Submission.objects.public().filter(thread_hash=self.thread_hash).order_by(
            '-submission_date', '-preprint__vn_nr')

    @property
    def thread_sequence_order(self):
        """Return the ordering of this Submission within its thread."""
        return self.thread.filter(submission_date__lt=self.submission_date).count() + 1

    @cached_property
    def other_versions(self):
        """Return other Submissions in the database in this thread."""
        return self.get_other_versions().order_by('-submission_date', '-preprint__vn_nr')

    def get_other_versions(self):
        """Return queryset of other Submissions with this thread."""
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

    @property
    def editorial_decision(self):
        """Returns the latest EditorialDecision (if it exists)."""
        if self.editorialdecision_set.exists():
            return self.editorialdecision_set.latest_version()
        return None


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
        """Summarize the SubmissionEvent's meta information."""
        return '%s: %s' % (str(self.submission), self.get_event_display())


class SubmissionTiering(models.Model):
    """A Fellow's quality tiering of a Submission for a given Journal, given during voting."""
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE,
                                   related_name='tierings')
    fellow = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE)
    for_journal = models.ForeignKey('journals.Journal', on_delete=models.CASCADE)
    tier = models.SmallIntegerField(choices=SUBMISSION_TIERS)
