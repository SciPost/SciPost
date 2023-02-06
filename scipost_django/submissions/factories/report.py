__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz

from faker import Faker

from scipost.models import Contributor
from common.helpers import random_scipost_report_doi_label

from submissions.constants import (
    REFEREE_QUALIFICATION,
    REPORT_STATUSES,
    RANKING_CHOICES,
    QUALITY_SPEC,
    REPORT_REC,
    STATUS_DRAFT,
    STATUS_UNVETTED,
    STATUS_VETTED,
)
from submissions.models import Report


class ReportFactory(factory.django.DjangoModelFactory):
    status = factory.Iterator(REPORT_STATUSES, getter=lambda c: c[0])
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    report_nr = factory.LazyAttribute(lambda o: o.submission.reports.count() + 1)
    date_submitted = factory.Faker("date_time_this_decade", tzinfo=pytz.utc)
    vetted_by = factory.Iterator(Contributor.objects.all())
    author = factory.Iterator(Contributor.objects.all())
    strengths = factory.Faker("paragraph")
    weaknesses = factory.Faker("paragraph")
    report = factory.Faker("paragraph")
    requested_changes = factory.Faker("paragraph")

    qualification = factory.Iterator(REFEREE_QUALIFICATION[1:], getter=lambda c: c[0])
    validity = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    significance = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    originality = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    clarity = factory.Iterator(RANKING_CHOICES[1:], getter=lambda c: c[0])
    formatting = factory.Iterator(QUALITY_SPEC[1:], getter=lambda c: c[0])
    grammar = factory.Iterator(QUALITY_SPEC[1:], getter=lambda c: c[0])
    recommendation = factory.Iterator(REPORT_REC[1:], getter=lambda c: c[0])

    remarks_for_editors = factory.Faker("paragraph")
    flagged = factory.Faker("boolean", chance_of_getting_true=10)
    anonymous = factory.Faker("boolean", chance_of_getting_true=75)

    class Meta:
        model = Report

    @classmethod
    def create(cls, **kwargs):
        if Contributor.objects.count() < 5:
            from scipost.factories import ContributorFactory

            ContributorFactory.create_batch(5)
        return super().create(**kwargs)


class DraftReportFactory(ReportFactory):
    status = STATUS_DRAFT
    vetted_by = None


class UnVettedReportFactory(ReportFactory):
    status = STATUS_UNVETTED
    vetted_by = None


class VettedReportFactory(ReportFactory):
    status = STATUS_VETTED
    needs_doi = True
    doideposit_needs_updating = factory.Faker("boolean")
    doi_label = factory.lazy_attribute(lambda n: random_scipost_report_doi_label())
    pdf_report = factory.Faker("file_name", extension="pdf")
