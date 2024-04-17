__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import datetime
import random
import factory

from affiliates.models import subsidy
from finances.constants import SUBSIDY_TYPES
from finances.models.pubfrac import PubFrac

from .models import (
    PeriodicReport,
    PeriodicReportType,
    Subsidy,
    SubsidyAttachment,
    SubsidyPayment,
    WorkLog,
)
from production.constants import PRODUCTION_ALL_WORK_LOG_TYPES
from scipost.factories import UserFactory

from common.faker import LazyAwareDate, LazyRandEnum, fake


# work_log.py
class WorkLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkLog

    user = factory.SubFactory(UserFactory)
    comments = factory.Faker("paragraph")
    log_type = LazyRandEnum(PRODUCTION_ALL_WORK_LOG_TYPES)
    duration = factory.LazyAttribute(lambda _: fake.duration())
    work_date = factory.Faker("date_this_year")
    created = factory.Faker("past_date", start_date="-1y")


class ProductionStreamWorkLogFactory(WorkLogFactory):
    class Params:
        stream = factory.SubFactory("production.factories.ProductionStreamFactory")

    content = factory.LazyAttribute(lambda self: self.stream)


# subsidy.py
class SubsidyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Subsidy

    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    subsidy_type = LazyRandEnum(SUBSIDY_TYPES)
    description = factory.Faker("sentence")
    amount = factory.Faker("pyint")
    amount_publicly_shown = True
    status = LazyRandEnum(SUBSIDY_TYPES)
    date_from = LazyAwareDate("date_this_decade")
    paid_on = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )
    date_until = factory.LazyAttribute(
        lambda self: fake.aware.date_between(start_date=self.date_from, end_date="+1y")
    )
    renewable = False


# subsidy_attachment.py
class SubsidyAttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubsidyAttachment

    subsidy = factory.SubFactory(SubsidyFactory)
    attachment = factory.django.FileField()
    git_url = factory.Faker("url")
    kind = LazyRandEnum(SubsidyAttachment.KIND_CHOICES)
    date = LazyAwareDate("date_this_year")
    description = factory.Faker("sentence")
    visibility = LazyRandEnum(SubsidyAttachment.VISIBILITY_FINADMINONLY)


# subsidy_payment.py
class SubsidyPaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SubsidyPayment

    subsidy = factory.SubFactory(SubsidyFactory)
    reference = factory.Faker("iban")
    amount = factory.Faker("pyint")
    date_scheduled = LazyAwareDate("date_this_year")
    invoice = factory.RelatedFactory(
        "finances.factories.SubsidyAttachmentFactory",
        factory_related_name="invoice_for",
        kind=SubsidyAttachment.KIND_INVOICE,
        description=factory.lazy_attribute(
            lambda self: "Invoice for " + self.subsidy.organization.name
        ),
    )
    proof_of_payment = factory.RelatedFactory(
        "finances.factories.SubsidyAttachmentFactory",
        factory_related_name="proof_of_payment_for",
        kind=SubsidyAttachment.KIND_PROOF_OF_PAYMENT,
        description=factory.lazy_attribute(
            lambda self: "Proof of payment for " + self.subsidy.organization.name
        ),
    )


# periodic_report.py
class PeriodicReportTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PeriodicReportType

    name = factory.Faker("word")
    description = factory.Faker("paragraph")


class PeriodicReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PeriodicReport

    _type = factory.SubFactory(PeriodicReportTypeFactory)
    _file = factory.django.FileField()
    created_on = LazyAwareDate("date_this_year")
    for_year = factory.Faker("year")


# pubfrac.py
class PubFracFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PubFrac

    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    publication = factory.SubFactory("journals.factories.JournalPublicationFactory")
    fraction = factory.Faker("pydecimal", left_digits=1, right_digits=3)
    compensated_by = factory.SubFactory(SubsidyFactory)
    cf_value = factory.LazyAttribute(
        lambda self: self.fraction * self.publication.expenditures
    )
