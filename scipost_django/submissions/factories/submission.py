__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz
import random

from faker import Faker

from scipost.constants import SCIPOST_APPROACHES
from scipost.models import Contributor
from comments.factories import SubmissionCommentFactory
from journals.models import Journal
from ontology.models import Specialty, AcademicField

from ..models import Submission, EditorialAssignment


class SubmissionFactory(factory.django.DjangoModelFactory):
    """
    Generate random basic Submission instances.
    """

    author_list = factory.Faker("name")
    submitted_by = factory.Iterator(Contributor.objects.all())
    submitted_to = factory.Iterator(Journal.objects.all())
    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph", nb_sentences=10)
    list_of_changes = factory.Faker("paragraph", nb_sentences=10)
    acad_field = factory.Iterator(AcademicField.objects.all())
    approaches = factory.Iterator(
        SCIPOST_APPROACHES,
        getter=lambda c: [
            c[0],
        ],
    )
    abstract = factory.Faker("paragraph")
    author_comments = factory.Faker("paragraph")
    remarks_for_editors = factory.Faker("paragraph")
    thread_hash = factory.Faker("uuid4")
    submission_date = factory.Faker("date_time_this_decade", tzinfo=pytz.utc)
    latest_activity = factory.LazyAttribute(
        lambda o: Faker().date_time_between(
            start_date=o.submission_date, end_date="now", tzinfo=pytz.UTC
        )
    )
    preprint = factory.SubFactory("preprints.factories.PreprintFactory")

    visible_public = True
    visible_pool = False

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
        if AcademicField.objects.count() < 10:
            from ontology.factories import AcademicFieldFactory

            AcademicFieldFactory.create_batch(10)
        if Specialty.objects.count() < 5:
            from ontology.factories import SpecialtyFactory

            SpecialtyFactory.create_batch(5)
        return super().create(**kwargs)

    @factory.post_generation
    def add_specialties(self, create, extracted, **kwargs):
        if create:
            self.specialties.set(Specialty.objects.order_by("?")[:3])

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        contribs = Contributor.objects.all()
        if self.editor_in_charge:
            contribs = contribs.exclude(id=self.editor_in_charge.id)
        contribs = contribs.order_by("?")[: random.randint(1, 6)]

        # Auto-add the submitter as an author
        self.submitted_by = contribs[0]
        self.author_list = ", ".join(
            ["%s %s" % (c.user.first_name, c.user.last_name) for c in contribs]
        )

        if not create:
            return

        # Add three random authors
        self.authors.add(*contribs)


class SeekingAssignmentSubmissionFactory(SubmissionFactory):
    """
    A new incoming Submission without any EIC assigned.
    """

    status = Submission.SEEKING_ASSIGNMENT
    visible_public = False
    visible_pool = True


class InRefereeingSubmissionFactory(SubmissionFactory):
    """
    A Submission with an EIC assigned, visible in the pool and refereeing in process.
    """

    status = Submission.IN_REFEREEING
    open_for_commenting = True
    open_for_reporting = True
    visible_public = True
    visible_pool = True
    editor_in_charge = factory.Iterator(Contributor.objects.all())
    # @factory.lazy_attribute
    # def editor_in_charge(self):
    #     return Contributor.objects.order_by('?').first()

    @factory.post_generation
    def eic_assignment(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import EditorialAssignmentFactory
            EditorialAssignmentFactory(submission=self, to=self.editor_in_charge)

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        from submissions.factories import (
            RefereeInvitationFactory,
            AcceptedRefereeInvitationFactory,
            FulfilledRefereeInvitationFactory,
        )
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
            from submissions.factories import EICRecommendationFactory
            EICRecommendationFactory(submission=self)


class ResubmittedSubmissionFactory(InRefereeingSubmissionFactory):
    """
    A Submission that has a newer Submission version in the database
    with a successive version number.
    """

    status = Submission.RESUBMITTED
    open_for_commenting = False
    open_for_reporting = False
    visible_public = True
    visible_pool = False

    @factory.post_generation
    def successive_submission(self, create, extracted, **kwargs):
        """
        Generate a second Submission that's the successive version of the resubmitted Submission
        """
        if create and extracted is not False:
            # Prevent infinite loops by checking the extracted argument
            ResubmissionFactory(
                thread_hash=self.thread_hash,
                previous_submission=False,
                visible_pool=True,
            )

    @factory.post_generation
    def gather_successor_data(self, create, extracted, **kwargs):
        """
        Gather some data from Submission with same arxiv id such that this Submission
        more or less looks like any regular real resubmission.
        """
        submission = (
            Submission.objects.filter(thread_hash=self.thread_hash)
            .exclude(pk=self.id)
            .first()
        )
        if not submission:
            return

        self.author_list = submission.author_list
        self.submitted_by = submission.submitted_by
        self.editor_in_charge = submission.editor_in_charge
        self.submitted_to = submission.submitted_to
        self.title = submission.title
        self.acad_field = submission.acad_field
        self.specialties.add(*submission.specialties.all())
        self.approaches = submission.approaches
        self.title = submission.title
        self.authors.set(self.authors.all())

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        """
        This Submission is deactivated for refereeing.
        """
        from submissions.factories import (
            FulfilledRefereeInvitationFactory,
            CancelledRefereeInvitationFactory,
        )
        for i in range(random.randint(0, 2)):
            FulfilledRefereeInvitationFactory(submission=self)

        for i in range(random.randint(1, 3)):
            CancelledRefereeInvitationFactory(submission=self)


class ResubmissionFactory(InRefereeingSubmissionFactory):
    """
    This Submission is a newer version of a Submission which is
    already known by the SciPost database.
    """

    status = Submission.REFEREEING_IN_PREPARATION
    open_for_commenting = True
    open_for_reporting = True
    visible_public = False
    visible_pool = True

    @factory.post_generation
    def previous_submission(self, create, extracted, **kwargs):
        if create and extracted is not False:
            # Prevent infinite loops by checking the extracted argument
            ResubmittedSubmissionFactory(
                thread_hash=self.thread_hash,
                successive_submission=False,
                visible_pool=False,
                visible_public=True,
            )

    @factory.post_generation
    def gather_predecessor_data(self, create, extracted, **kwargs):
        """
        Gather some data from Submission with same arxiv id such that this Submission
        more or less looks like any regular real resubmission.
        """
        submission = (
            Submission.objects.filter(thread_hash=self.thread_hash)
            .exclude(pk=self.id)
            .first()
        )
        if not submission:
            return

        self.author_list = submission.author_list
        self.submitted_by = submission.submitted_by
        self.editor_in_charge = submission.editor_in_charge
        self.submitted_to = submission.submitted_to
        self.title = submission.title
        self.acad_field = submission.acad_field
        self.specialties.add(*submission.specialties.all())
        self.approaches = submission.approaches
        self.title = submission.title
        self.authors.set(self.authors.all())

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        """
        Referees for resubmissions are invited once the cycle has been chosen.
        """
        pass


class PublishedSubmissionFactory(InRefereeingSubmissionFactory):
    status = Submission.PUBLISHED
    open_for_commenting = False
    open_for_reporting = False
    visible_public = True
    visible_pool = False

    @factory.post_generation
    def generate_publication(self, create, extracted, **kwargs):
        if create and extracted is not False:
            from journals.factories import PublicationFactory
            PublicationFactory(
                journal=self.submitted_to.doi_label,
                accepted_submission=self,
                title=self.title,
                author_list=self.author_list,
            )

    @factory.post_generation
    def eic_assignment(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import EditorialAssignmentFactory
            EditorialAssignmentFactory(
                submission=self,
                to=self.editor_in_charge,
                status=EditorialAssignment.STATUS_COMPLETED,
            )

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        from submissions.factories import (
            FulfilledRefereeInvitationFactory,
            CancelledRefereeInvitationFactory
        )
        
        for i in range(random.randint(2, 4)):
            FulfilledRefereeInvitationFactory(submission=self)
        for i in range(random.randint(0, 2)):
            CancelledRefereeInvitationFactory(submission=self)
