import factory
import datetime
import pytz

from django.utils import timezone

from common.helpers import random_digits
from journals.constants import SCIPOST_JOURNALS
from submissions.factories import PublishedSubmissionFactory

from .models import Journal, Volume, Issue, Publication

from faker import Faker


class JournalFactory(factory.django.DjangoModelFactory):
    name = factory.Iterator(SCIPOST_JOURNALS, getter=lambda c: c[0])
    doi_label = factory.Iterator(SCIPOST_JOURNALS, getter=lambda c: c[0])
    issn = factory.lazy_attribute(lambda n: random_digits(8))

    class Meta:
        model = Journal
        django_get_or_create = ('name', 'doi_label',)


class VolumeFactory(factory.django.DjangoModelFactory):
    in_journal = factory.SubFactory(JournalFactory)
    number = factory.Sequence(lambda n: n + 1)
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        self.doi_label = self.in_journal.doi_label + '.' + str(self.number)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        timezone.now()
        self.start_date = Faker().date_time_between(start_date="-3y", end_date="now",
                                                    tzinfo=pytz.UTC)
        self.until_date = self.start_date + datetime.timedelta(weeks=26)

    class Meta:
        model = Volume
        django_get_or_create = ('in_journal', 'number')


class IssueFactory(factory.django.DjangoModelFactory):
    in_volume = factory.SubFactory(VolumeFactory)
    number = factory.Sequence(lambda n: n + 1)
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        self.doi_label = self.in_volume.doi_label + '.' + str(self.number)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        timezone.now()
        self.start_date = Faker().date_time_between(start_date=self.in_volume.start_date,
                                                    end_date=self.in_volume.until_date,
                                                    tzinfo=pytz.UTC)
        self.until_date = self.start_date + datetime.timedelta(weeks=4)

    class Meta:
        model = Issue
        django_get_or_create = ('in_volume', 'number')


class PublicationFactory(factory.django.DjangoModelFactory):
    accepted_submission = factory.SubFactory(PublishedSubmissionFactory)
    paper_nr = factory.Sequence(lambda n: n)
    pdf_file = Faker().file_name(extension='pdf')
    in_issue = factory.SubFactory(IssueFactory)
    submission_date = factory.Faker('date')
    acceptance_date = factory.Faker('date')
    publication_date = factory.Faker('date')
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        paper_nr = self.in_issue.publication_set.count() + 1
        self.paper_nr = paper_nr
        self.doi_label = self.in_issue.doi_label + '.' + str(paper_nr).rjust(3, '0')

    @factory.post_generation
    def submission_data(self, create, extracted, **kwargs):
        # Content
        self.discipline = self.accepted_submission.discipline
        self.domain = self.accepted_submission.domain
        self.subject_area = self.accepted_submission.subject_area
        self.title = self.accepted_submission.title
        self.abstract = self.accepted_submission.abstract

        # Authors
        self.author_list = self.accepted_submission.author_list
        self.authors.add(*self.accepted_submission.authors.all())
        self.first_author = self.accepted_submission.authors.first()
        self.authors_claims.add(*self.accepted_submission.authors_claims.all())
        self.authors_false_claims.add(*self.accepted_submission.authors_false_claims.all())

        # Dates
        self.submission_date = self.accepted_submission.latest_activity
        self.acceptance_date = self.accepted_submission.latest_activity
        self.publication_date = self.accepted_submission.latest_activity
        self.latest_activity = self.accepted_submission.latest_activity

    class Meta:
        model = Publication
        django_get_or_create = ('accepted_submission', )
