__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory

from common.faker import LazyRandEnum

from ..models import Qualification


class QualificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Qualification
        django_get_or_create = ("submission", "fellow")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    fellow = factory.SubFactory(
        "colleges.factories.FellowFactory",
        profile__acad_field=factory.SelfAttribute("...submission.acad_field"),
    )

    expertise_level = LazyRandEnum(Qualification.EXPERTISE_LEVEL_CHOICES)
    comments = factory.Faker("paragraph")
