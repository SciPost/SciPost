__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz
import random

from comments.factories import SubmissionCommentFactory
from scipost.constants import SCIPOST_SUBJECT_AREAS, SCIPOST_APPROACHES
from scipost.models import Contributor
from journals.models import Journal
from common.helpers import random_scipost_report_doi_label

from .constants import (
    STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_INCOMING, STATUS_PUBLISHED,
    STATUS_RESUBMITTED, STATUS_VETTED, REFEREE_QUALIFICATION, RANKING_CHOICES, QUALITY_SPEC,
    REPORT_REC, REPORT_STATUSES, STATUS_UNVETTED, STATUS_DRAFT, ASSIGNMENT_STATUSES)
from .models import Submission, Report, RefereeInvitation, EICRecommendation, EditorialAssignment

from faker import Faker


class SubmissionFactory(factory.django.DjangoModelFactory):
    """
    Generate random basic Submission instances.
    """

    author_list = factory.Faker('name')
    submitted_by = factory.SubFactory('scipost.factories.ContributorFactory')
    submitted_to = factory.SubFactory('journals.factories.JournalFactory')
    title = factory.Faker('sentence')
    abstract = factory.Faker('paragraph', nb_sentences=10)
    list_of_changes = factory.Faker('paragraph', nb_sentences=10)
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    approaches = factory.Iterator(SCIPOST_APPROACHES, getter=lambda c: [c[0],])
    abstract = factory.Faker('paragraph')
    author_comments = factory.Faker('paragraph')
    remarks_for_editors = factory.Faker('paragraph')
    thread_hash = factory.Faker('uuid4')
    is_current = True
    submission_date = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    latest_activity = factory.LazyAttribute(lambda o: Faker().date_time_between(
        start_date=o.submission_date, end_date="now", tzinfo=pytz.UTC))
    preprint = factory.SubFactory('preprints.factories.PreprintFactory')

    class Meta:
        model = Submission

    @classmethod
    def create(cls, **kwargs):
        if Contributor.objects.count() < 5:
            from scipost.factories import ContributorFactory
            ContributorFactory.create_batch(5)
        if Journal.objects.count() < 3:
            from journals.factories import JournalFactory
            JournalFactory.create_batch(3)
        return super().create(**kwargs)

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        contribs = Contributor.objects.all()
        if self.editor_in_charge:
            contribs = contribs.exclude(id=self.editor_in_charge.id)
        contribs = contribs.order_by('?')[:random.randint(1, 6)]

        # Auto-add the submitter as an author
        self.submitted_by = contribs[0]
        self.author_list = ', '.join([
            '%s %s' % (c.user.first_name, c.user.last_name) for c in contribs])

        if not create:
            return

        # Add three random authors
        self.authors.add(*contribs)


class UnassignedSubmissionFactory(SubmissionFactory):
    """
    A new incoming Submission without any EIC assigned.
    """
    status = STATUS_UNASSIGNED


class EICassignedSubmissionFactory(SubmissionFactory):
    """
    A Submission with an EIC assigned, visible in the pool and refereeing in process.
    """
    status = STATUS_EIC_ASSIGNED
    open_for_commenting = True
    open_for_reporting = True
    editor_in_charge = factory.SubFactory('scipost.factories.ContributorFactory')
    # @factory.lazy_attribute
    # def editor_in_charge(self):
    #     return Contributor.objects.order_by('?').first()

    @factory.post_generation
    def eic_assignment(self, create, extracted, **kwargs):
        if create:
            EditorialAssignmentFactory(submission=self, to=self.editor_in_charge)

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        for i in range(random.randint(1, 3)):
            RefereeInvitationFactory(submission=self)

        for i in range(random.randint(0, 2)):
            AcceptedRefereeInvitationFactory(submission=self)

        for i in range(random.randint(0, 2)):
            FulfilledRefereeInvitationFactory(submission=self)

    @factory.post_generation
    def comments(self, create, extracted, **kwargs):
        if create:
            for i in range(random.randint(0, 3)):
                SubmissionCommentFactory(content_object=self)

    @factory.post_generation
    def eic_recommendation(self, create, extracted, **kwargs):
        if create:
            EICRecommendationFactory(submission=self)


class ResubmittedSubmissionFactory(EICassignedSubmissionFactory):
    """
    A Submission that has a newer Submission version in the database
    with a successive version number.
    """
    status = STATUS_RESUBMITTED
    open_for_commenting = False
    open_for_reporting = False
    is_current = False

    @factory.post_generation
    def successive_submission(self, create, extracted, **kwargs):
        """
        Generate a second Submission that's the successive version of the resubmitted Submission
        """
        if create and extracted is not False:
            # Prevent infinite loops by checking the extracted argument
            ResubmissionFactory(preprint__identifier_wo_vn_nr=self.preprint.identifier_wo_vn_nr,
                                previous_submission=False)

    @factory.post_generation
    def gather_successor_data(self, create, extracted, **kwargs):
        """
        Gather some data from Submission with same arxiv id such that this Submission
        more or less looks like any regular real resubmission.
        """
        submission = Submission.objects.filter(
            preprint__identifier_wo_vn_nr=self.preprint.identifier_wo_vn_nr).exclude(
            preprint__vn_nr=self.preprint.vn_nr).first()
        if not submission:
            return

        self.author_list = submission.author_list
        self.submitted_by = submission.submitted_by
        self.editor_in_charge = submission.editor_in_charge
        self.submitted_to = submission.submitted_to
        self.title = submission.title
        self.subject_area = submission.subject_area
        self.approaches = submission.approaches
        self.title = submission.title
        self.authors.set(self.authors.all())

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        """
        This Submission is deactivated for refereeing.
        """
        for i in range(random.randint(0, 2)):
            FulfilledRefereeInvitationFactory(submission=self)

        for i in range(random.randint(1, 3)):
            CancelledRefereeInvitationFactory(submission=self)


class ResubmissionFactory(EICassignedSubmissionFactory):
    """
    This Submission is a newer version of a Submission which is
    already known by the SciPost database.
    """
    status = STATUS_INCOMING
    open_for_commenting = True
    open_for_reporting = True
    vn_nr = 2

    @factory.post_generation
    def previous_submission(self, create, extracted, **kwargs):
        if create and extracted is not False:
            # Prevent infinite loops by checking the extracted argument
            ResubmittedSubmissionFactory(
                preprint__identifier_wo_vn_nr=self.preprint.identifier_wo_vn_nr,
                successive_submission=False)

    @factory.post_generation
    def gather_predecessor_data(self, create, extracted, **kwargs):
        """
        Gather some data from Submission with same arxiv id such that this Submission
        more or less looks like any regular real resubmission.
        """
        submission = Submission.objects.filter(
            identifier_wo_vn_nr=self.preprint.identifier_wo_vn_nr).exclude(
            preprint__vn_nr=self.preprint.vn_nr).first()
        if not submission:
            return

        self.author_list = submission.author_list
        self.submitted_by = submission.submitted_by
        self.editor_in_charge = submission.editor_in_charge
        self.submitted_to = submission.submitted_to
        self.title = submission.title
        self.subject_area = submission.subject_area
        self.approaches = submission.approaches
        self.title = submission.title
        self.authors.set(self.authors.all())

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        """
        Referees for resubmissions are invited once the cycle has been chosen.
        """
        pass


class PublishedSubmissionFactory(EICassignedSubmissionFactory):
    status = STATUS_PUBLISHED
    open_for_commenting = False
    open_for_reporting = False

    @factory.post_generation
    def generate_publication(self, create, extracted, **kwargs):
        if create and extracted is not False:
            from journals.factories import PublicationFactory
            PublicationFactory(
                journal=self.submitted_to.doi_label,
                accepted_submission=self, title=self.title, author_list=self.author_list)

    @factory.post_generation
    def eic_assignment(self, create, extracted, **kwargs):
        if create:
            EditorialAssignmentFactory(submission=self, to=self.editor_in_charge, completed=True)

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        for i in range(random.randint(2, 4)):
            FulfilledRefereeInvitationFactory(submission=self)

        for i in range(random.randint(0, 2)):
            CancelledRefereeInvitationFactory(submission=self)


class ReportFactory(factory.django.DjangoModelFactory):
    status = factory.Iterator(REPORT_STATUSES, getter=lambda c: c[0])
    submission = factory.SubFactory('submissions.factories.SubmissionFactory')
    report_nr = factory.LazyAttribute(lambda o: o.submission.reports.count() + 1)
    date_submitted = factory.Faker('date_time_this_decade', tzinfo=pytz.utc)
    vetted_by = factory.SubFactory('scipost.factories.ContributorFactory')
    author = factory.SubFactory('scipost.factories.ContributorFactory')
    strengths = factory.Faker('paragraph')
    weaknesses = factory.Faker('paragraph')
    report = factory.Faker('paragraph')
    requested_changes = factory.Faker('paragraph')

    qualification = factory.Iterator(REFEREE_QUALIFICATION[1:], getter=lambda c: c[0])
    validity = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    significance = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    originality = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    clarity = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    formatting = factory.Iterator(QUALITY_SPEC[1:], getter=lambda c: c[0])
    grammar = factory.Iterator(QUALITY_SPEC[1:], getter=lambda c: c[0])
    recommendation = factory.Iterator(REPORT_REC[1:], getter=lambda c: c[0])

    remarks_for_editors = factory.Faker('paragraph')
    flagged = factory.Faker('boolean', chance_of_getting_true=10)
    anonymous = factory.Faker('boolean', chance_of_getting_true=75)

    class Meta:
        model = Report


class DraftReportFactory(ReportFactory):
    status = STATUS_DRAFT
    vetted_by = None


class UnVettedReportFactory(ReportFactory):
    status = STATUS_UNVETTED
    vetted_by = None


class VettedReportFactory(ReportFactory):
    status = STATUS_VETTED
    needs_doi = True
    doideposit_needs_updating = factory.Faker('boolean')
    doi_label = factory.lazy_attribute(lambda n: random_scipost_report_doi_label())
    pdf_report = factory.Faker('file_name', extension='pdf')


class RefereeInvitationFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory('submissions.factories.SubmissionFactory')
    referee = factory.lazy_attribute(lambda o: Contributor.objects.exclude(
        id__in=o.submission.authors.all()).order_by('?').first())

    title = factory.lazy_attribute(lambda o: o.referee.title)
    first_name = factory.lazy_attribute(lambda o: o.referee.user.first_name)
    last_name = factory.lazy_attribute(lambda o: o.referee.user.last_name)
    email_address = factory.lazy_attribute(lambda o: o.referee.user.email)
    date_invited = factory.lazy_attribute(lambda o: o.submission.latest_activity)
    nr_reminders = factory.lazy_attribute(lambda o: random.randint(0, 4))
    date_last_reminded = factory.lazy_attribute(lambda o: o.submission.latest_activity)

    invitation_key = factory.Faker('md5')
    invited_by = factory.lazy_attribute(lambda o: o.submission.editor_in_charge)

    class Meta:
        model = RefereeInvitation


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    accepted = True
    date_responded = factory.lazy_attribute(lambda o: Faker().date_time_between(
        start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC))

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            VettedReportFactory(submission=self.submission, author=self.referee)


class FulfilledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = True
    date_responded = factory.lazy_attribute(lambda o: Faker().date_time_between(
        start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC))

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            VettedReportFactory(submission=self.submission, author=self.referee)


class CancelledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = False
    cancelled = True
    date_responded = factory.lazy_attribute(lambda o: Faker().date_time_between(
        start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC))


class EICRecommendationFactory(factory.django.DjangoModelFactory):
    submission = factory.Iterator(Submission.objects.all())
    date_submitted = factory.lazy_attribute(lambda o: Faker().date_time_between(
        start_date=o.submission.submission_date, end_date="now", tzinfo=pytz.UTC))
    remarks_for_authors = factory.Faker('paragraph')
    requested_changes = factory.Faker('paragraph')
    remarks_for_editorial_college = factory.Faker('paragraph')
    recommendation = factory.Iterator(REPORT_REC[1:], getter=lambda c: c[0])
    version = 1
    active = True

    class Meta:
        model = EICRecommendation


class EditorialAssignmentFactory(factory.django.DjangoModelFactory):
    """
    An EditorialAssignmentFactory should always have a `submission` explicitly assigned. This will
    mostly be done using the post_generation hook in any SubmissionFactory.
    """
    submission = None
    to = factory.SubFactory('scipost.factories.ContributorFactory')
    status = factory.Iterator(ASSIGNMENT_STATUSES, getter=lambda c: c[0])
    date_created = factory.lazy_attribute(lambda o: o.submission.latest_activity)
    date_answered = factory.lazy_attribute(lambda o: o.submission.latest_activity)

    class Meta:
        model = EditorialAssignment
