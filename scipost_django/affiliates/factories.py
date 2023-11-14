__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.utils.text import slugify
import factory

from common.faker import LazyAwareDate, fake
from common.helpers import random_external_doi
from ontology.factories import AcademicFieldFactory, SpecialtyFactory

from .models import AffiliateJournal
from .models.pubfraction import AffiliatePubFraction
from .models.publisher import AffiliatePublisher
from .models.publication import AffiliatePublication
from .models.subsidy import AffiliateJournalYearSubsidy


class AffiliatePublisherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffiliatePublisher

    name = factory.Faker("company")


class AffiliateJournalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffiliateJournal

    publisher = factory.SubFactory(AffiliatePublisherFactory)
    name = factory.Faker("company")
    short_name = factory.LazyAttribute(
        lambda self: "".join(w[0].upper() for w in self.name.split()[:1])
    )
    slug = factory.LazyAttribute(lambda self: slugify(self.name))
    acad_field = factory.SubFactory(AcademicFieldFactory)
    homepage = factory.Faker("url")
    logo_svg = factory.django.ImageField()
    logo = factory.django.ImageField()
    cost_info = {}

    @factory.post_generation
    def specialties(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.specialties.add(*extracted)
        else:
            specialties = SpecialtyFactory.create_batch(3, acad_field=self.acad_field)
            self.specialties.add(*specialties)


class AffiliatePubFractionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffiliatePubFraction

    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    publication = factory.SubFactory("affiliates.factories.AffiliatePublicationFactory")
    fraction = factory.Faker("pydecimal", left_digits=1, right_digits=3)


class AffiliatePublicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffiliatePublication

    doi = factory.LazyAttribute(lambda _: random_external_doi())
    _metadata_crossref = {}
    journal = factory.SubFactory(AffiliateJournalFactory)
    publication_date = LazyAwareDate("date_this_year")


class AffiliateJournalYearSubsidyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AffiliateJournalYearSubsidy

    journal = factory.SubFactory(AffiliateJournalFactory)
    organization = factory.SubFactory("organizations.factories.OrganizationFactory")
    description = factory.Faker("sentence")
    amount = factory.Faker("pyint")
    year = factory.Faker("year")
