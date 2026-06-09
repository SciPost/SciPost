__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models.signals import post_save
import factory

from common.faker import LazyAwareDateOffset, LazyRandEnum, LazyRandInstance, fake
from scipost.factories import ContributorFactory

from common.helpers import random_scipost_report_doi_label

from submissions.constants import (
    REFEREE_QUALIFICATION,
    REPORT_MAJOR_REV,
    REPORT_MINOR_REV,
    REPORT_STATUSES,
    RANKING_CHOICES,
    QUALITY_SPEC,
    REPORT_REC,
    STATUS_DRAFT,
    STATUS_UNVETTED,
    STATUS_VETTED,
)
from submissions.models import Report


@factory.django.mute_signals(post_save)
class ReportFactory(factory.django.DjangoModelFactory[Report]):
    class Meta:
        model = Report

    status = LazyRandEnum(REPORT_STATUSES)
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    report_nr = factory.LazyAttribute(lambda self: self.submission.reports.count() + 1)
    date_submitted = LazyAwareDateOffset("submission.submission_date", "+1y")

    @factory.lazy_attribute
    def vetted_by(self):
        if self.status not in [STATUS_DRAFT, STATUS_UNVETTED]:
            return self.submission.editor_in_charge

    author = factory.SubFactory(ContributorFactory)
    strengths = factory.Faker("paragraph")
    weaknesses = factory.Faker("paragraph")
    report = factory.Faker("paragraph")
    requested_changes = factory.Faker("paragraph")

    qualification = LazyRandEnum(REFEREE_QUALIFICATION)
    validity = LazyRandEnum(RANKING_CHOICES)
    significance = LazyRandEnum(RANKING_CHOICES)
    originality = LazyRandEnum(RANKING_CHOICES)
    clarity = LazyRandEnum(RANKING_CHOICES)
    formatting = LazyRandEnum(QUALITY_SPEC)
    grammar = LazyRandEnum(QUALITY_SPEC)
    recommendation = LazyRandEnum(REPORT_REC)

    remarks_for_editors = factory.Faker("paragraph")
    flagged = factory.Faker("boolean", chance_of_getting_true=10)
    anonymous = factory.Faker("boolean", chance_of_getting_true=75)


class DraftReportFactory(ReportFactory):
    status = STATUS_DRAFT
    vetted_by = None


class UnVettedReportFactory(ReportFactory):
    status = STATUS_UNVETTED
    vetted_by = None


class VettedReportFactory(ReportFactory):
    status = STATUS_VETTED
    needs_doi = True
    doi_label = factory.LazyAttribute(lambda _: random_scipost_report_doi_label)
    pdf_report = factory.django.FileField(filename="report.pdf")

    class Params:
        revision = factory.Trait(
            recommendation=fake.random_element([REPORT_MINOR_REV, REPORT_MAJOR_REV]),
        )

    @factory.post_generation
    def author_reply(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            extracted.content_object = self
            extracted.save()
            return

        from comments.factories import ReplyCommentFactory

        ReplyCommentFactory(
            content_object=self,
            is_author_reply=True,
            vetted_by=self.submission.editor_in_charge,
            author=LazyRandInstance(self.submission.authors.all()),
        )
