__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory

from common.faker import LazyAwareDate, LazyRandEnum
from submissions.constants import ED_COMM_CHOICES

from ..models import EditorialCommunication


class EditorialCommunicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditorialCommunication

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    referee = factory.SubFactory("scipost.factories.ContributorFactory")
    comtype = LazyRandEnum(ED_COMM_CHOICES)
    timestamp = LazyAwareDate("date_time_this_year")
    text = factory.Faker("paragraph")
