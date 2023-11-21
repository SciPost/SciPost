__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.faker import LazyRandEnum, fake

from ..models import EditorialAssignment


class EditorialAssignmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialAssignment
        django_get_or_create = ("submission", "to")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    to = factory.SubFactory("scipost.factories.ContributorFactory")
    status = LazyRandEnum(EditorialAssignment.ASSIGNMENT_STATUSES)

    date_created = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.submission.submission_date, end_date="+60d"
        )
    )
    date_invited = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.date_created, end_date="+10d"
        )
    )
    date_answered = factory.LazyAttribute(
        lambda self: fake.aware.date_between(
            start_date=self.date_invited, end_date="+10d"
        )
    )
