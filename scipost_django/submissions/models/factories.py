__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory
from common.faker import LazyRandEnum
from journals.factories import JournalFactory
from submissions.factories.submission import SubmissionFactory
from submissions.models.decision import EditorialDecision


class EditorialDecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialDecision
        django_get_or_create = ("submission", "for_journal")

    submission = factory.SubFactory(SubmissionFactory)
    for_journal = factory.SubFactory(JournalFactory)
    decision = LazyRandEnum(EditorialDecision.EDITORIAL_DECISION_STATUSES)
    taken_on = factory.Faker("date_this_decade")
    remarks_for_authors = factory.Faker("paragraph")
    status = LazyRandEnum(EditorialDecision.EDITORIAL_DECISION_STATUSES)
