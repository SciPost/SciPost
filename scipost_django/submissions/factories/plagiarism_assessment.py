__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory

from common.faker import LazyAwareDateOffset, LazyRandEnum

from ..models.plagiarism_assessment import (
    PlagiarismAssessment,
    InternalPlagiarismAssessment,
    iThenticatePlagiarismAssessment,
)


class PlagiarismAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlagiarismAssessment
        abstract = True
        django_get_or_create = ("submission",)

    status = LazyRandEnum(PlagiarismAssessment.STATUS_CHOICES)
    date_set = LazyAwareDateOffset("submission.submission_date", "+5d")

    comments_for_edadmin = factory.Faker("paragraph")
    comments_for_authors = factory.Faker("paragraph")


class InternalPlagiarismAssessmentFactory(PlagiarismAssessmentFactory):
    class Meta:
        model = InternalPlagiarismAssessment

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")


class iThenticatePlagiarismAssessmentFactory(PlagiarismAssessmentFactory):
    class Meta:
        model = iThenticatePlagiarismAssessment

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
