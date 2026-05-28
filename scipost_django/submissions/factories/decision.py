__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory

from common.faker import LazyAwareDateOffset, LazyRandEnum
from submissions.constants import EDITORIAL_DECISION_CHOICES
from ..models import EditorialDecision


class EditorialDecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialDecision
        django_get_or_create = ("submission", "version")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    for_journal = factory.SubFactory("journals.factories.JournalFactory")
    taken_on = LazyAwareDateOffset("submission.submission_date", "+2M")

    remarks_for_authors = factory.Faker("paragraph")
    remarks_for_editorial_college = factory.Faker("paragraph")

    decision = LazyRandEnum(EDITORIAL_DECISION_CHOICES)
    status = EditorialDecision.FIXED_AND_ACCEPTED

    version = factory.LazyAttribute(
        lambda self: self.submission.editorialdecision_set.count() + 1
    )
