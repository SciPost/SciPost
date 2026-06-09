__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz
import random

from common.faker import LazyRandEnum, fake
from journals.factories import JournalFactory
from ontology.factories import AcademicFieldFactory
from organizations.factories import OrganizationFactory
from preprints.factories import PreprintFactory

from scipost.constants import SCIPOST_APPROACHES
from scipost.factories import ContributorFactory
from scipost.models import Contributor
from comments.factories import SubmissionCommentFactory

from ..models.submission import *


class SubmissionFactory(factory.django.DjangoModelFactory):
    """
    Generate random basic Submission instances.
    """

    submitted_by = factory.SubFactory(ContributorFactory)
    author_list = factory.LazyAttribute(
        lambda self: self.submitted_by.profile.full_name
    )
    submitted_to = factory.SubFactory(JournalFactory)

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph", nb_sentences=10)

    acad_field = factory.SubFactory(AcademicFieldFactory)
    approaches = LazyRandEnum(SCIPOST_APPROACHES, repeat=2)

    list_of_changes = factory.Faker("paragraph", nb_sentences=10)
    author_comments = factory.Faker("paragraph")
    remarks_for_editors = factory.Faker("paragraph")

    submission_date = factory.Faker("date_time_this_decade", tzinfo=pytz.utc)
    latest_activity = factory.LazyAttribute(
        lambda self: fake.date_time_between(
            start_date=self.submission_date, end_date="now", tzinfo=pytz.UTC
        )
    )

    thread_hash = factory.Faker("md5")
    preprint = factory.SubFactory(PreprintFactory)

    visible_public = True
    visible_pool = False

    class Meta:
        model = Submission
        django_get_or_create = ("preprint",)

    @factory.post_generation
    @set_or_create_consistent_related_field(
        SpecialtyFactory, (1, 4), {"acad_field": "acad_field"}
    )
    def specialties(self, create, extracted, **kwargs):
        pass

    @factory.post_generation
    @set_or_create_consistent_related_field(
        ContributorFactory, (1, 4), {"profile__acad_field": "acad_field"}
    )
    def authors(self, create, extracted, **kwargs):
        self.author_list = ", ".join(
            [a.profile.full_name for a in self.authors.all().select_related("profile")]
        )


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
        from submissions.factories import EditorialAssignmentFactory

        if not create:
            return
        if extracted:
            if isinstance(extracted, Contributor):
                self.editor_in_charge = extracted
                EditorialAssignmentFactory(
                    submission=self,
                    to=self.editor_in_charge,
                    status=EditorialAssignment.STATUS_ACCEPTED,
                )
            elif isinstance(extracted, EditorialAssignment):
                self.editor_in_charge = extracted.to
                extracted.submission = self
                extracted.status = EditorialAssignment.STATUS_ACCEPTED
                extracted.save()
        else:
            from colleges.factories import FellowFactory

            self.editor_in_charge = FellowFactory(profile__acad_field=self.acad_field)

            EditorialAssignmentFactory(
                submission=self,
                to=self.editor_in_charge,
                status=EditorialAssignment.STATUS_ACCEPTED,
            )

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

    # @factory.post_generation
    # def generate_publication(self, create, extracted, **kwargs):
    #     if create and extracted is not False:
    #         from journals.factories import JournalPublicationFactory

    #         JournalPublicationFactory(
    #             in_journal=self.submitted_to,
    #             accepted_submission=self,
    #             title=self.title,
    #             author_list=self.author_list,
    #         )

    @factory.post_generation
    def eic_assignment_completed(self, create, extracted, **kwargs):
        assignment = self.editorial_assignments.first()
        assignment.status = EditorialAssignment.STATUS_COMPLETED
        assignment.save()

    @factory.post_generation
    def referee_invites(self, create, extracted, **kwargs):
        from submissions.factories import (
            FulfilledRefereeInvitationFactory,
            CancelledRefereeInvitationFactory,
        )

        for i in range(random.randint(2, 4)):
            FulfilledRefereeInvitationFactory(submission=self)
        for i in range(random.randint(0, 2)):
            CancelledRefereeInvitationFactory(submission=self)


class SubmissionAuthorProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionAuthorProfile

    submission = factory.SubFactory(SubmissionFactory)
    profile = factory.SubFactory("profiles.factories.ProfileFactory")
    order = factory.LazyAttribute(
        lambda self: self.submission.author_profiles.count() + 1
    )

    @factory.post_generation
    def affiliations(self, create, extracted, **kwargs):
        if create:
            return
        if extracted:
            for affiliation in extracted:
                self.affiliations.add(affiliation)
        else:
            self.affiliations.add(
                *OrganizationFactory.create_batch(random.randint(1, 3))
            )


class SubmissionEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionEvent

    submission = factory.SubFactory(SubmissionFactory)
    event = LazyRandEnum(EVENT_TYPES)
    text = factory.Faker("paragraph")


class SubmissionTieringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubmissionTiering

    submission = factory.SubFactory(SubmissionFactory)
    fellow = factory.SubFactory(ContributorFactory)
    for_journal = factory.SelfAttribute("submission.submitted_to")
    tier = LazyRandEnum(SUBMISSION_TIERS)
