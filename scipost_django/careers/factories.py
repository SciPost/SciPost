from django.utils.text import slugify
import factory

from common.faker import LazyAwareDate, LazyRandEnum
from scipost.constants import TITLE_CHOICES

from .models import JobApplication, JobOpening


class JobOpeningFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobOpening

    title = factory.Faker("job")
    short_description = factory.Faker("sentence")
    description = factory.Faker("paragraph")
    application_deadline = LazyAwareDate("date_this_year")
    status = LazyRandEnum(JobOpening.JOBOPENING_STATUSES)
    announced = LazyAwareDate("date_this_year")
    slug = factory.LazyAttribute(lambda self: slugify(self.title))


class JobApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobApplication

    uuid = factory.Faker("uuid4")
    status = LazyRandEnum(JobApplication.JOBAPP_STATUSES)
    last_updated = LazyAwareDate("date_this_year")
    job_opening = factory.SubFactory(JobOpeningFactory)
    date_received = LazyAwareDate("date_this_year")
    title = LazyRandEnum(TITLE_CHOICES)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    motivation = factory.django.FileField()
    cv = factory.django.FileField()
