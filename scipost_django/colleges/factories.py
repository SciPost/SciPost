__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
from django.utils.text import slugify
from colleges.models.nomination import FellowshipNomination
from common.faker import LazyAwareDate
from ontology.factories import AcademicFieldFactory
from profiles.factories import ProfileFactory
from scipost.factories import ContributorFactory

from .models import College, Fellowship


class CollegeFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("word")
    acad_field = factory.SubFactory(AcademicFieldFactory)
    slug = factory.LazyAttribute(lambda self: slugify(self.name))
    order = factory.Sequence(lambda n: College.objects.count() + 1)

    class Meta:
        model = College


class BaseFellowshipFactory(factory.django.DjangoModelFactory):
    college = factory.SubFactory(CollegeFactory)
    contributor = factory.SubFactory(ContributorFactory)
    start_date = factory.Faker("date_this_year")
    until_date = factory.Faker("date_between", start_date="now", end_date="+2y")

    class Meta:
        model = Fellowship
        django_get_or_create = ("contributor", "start_date")
        abstract = True


class FellowshipFactory(BaseFellowshipFactory):
    status = "regular"


class GuestFellowshipFactory(BaseFellowshipFactory):
    status = "guest"


class SeniorFellowshipFactory(BaseFellowshipFactory):
    status = "senior"


class FellowshipNominationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FellowshipNomination

    college = factory.SubFactory(CollegeFactory)
    profile = factory.SubFactory(ProfileFactory)
    nominated_by = factory.SubFactory(ContributorFactory)
    nominated_on = LazyAwareDate("date_time_this_year")
    nominator_comments = factory.Faker("text")
    fellowship = None


class RegisteredFellowshipNominationFactory(FellowshipNominationFactory):
    @factory.post_generation
    def create_profile_contributor(self, create, extracted, **kwargs):
        if not create:
            return
        self.profile.contributor = ContributorFactory.from_profile(self.profile)
        self.profile.save()


class SuccessfulFellowshipNominationFactory(RegisteredFellowshipNominationFactory):
    @factory.post_generation
    def fellowship(self, create, extracted, **kwargs):
        if not create:
            return
        self.fellowship = FellowshipFactory(
            contributor=self.profile.contributor, college=self.college
        )
        self.fellowship.save()
