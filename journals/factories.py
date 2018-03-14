import factory
import datetime
import pytz

from common.helpers import random_digits
from journals.constants import SCIPOST_JOURNALS, SCIPOST_JOURNAL_PHYSICS_LECTURE_NOTES,\
    ISSUES_AND_VOLUMES, INDIVIDUAL_PUBLCATIONS, PUBLICATION_PUBLISHED
from submissions.factories import PublishedSubmissionFactory

from .models import Journal, Volume, Issue, Publication

from faker import Faker


class JournalFactory(factory.django.DjangoModelFactory):
    name = factory.Iterator(SCIPOST_JOURNALS, getter=lambda c: c[0])
    doi_label = factory.Iterator(SCIPOST_JOURNALS, getter=lambda c: c[0])
    issn = factory.lazy_attribute(lambda n: random_digits(8))

    @factory.post_generation
    def structure(self, create, extracted, **kwargs):
        if self.name == SCIPOST_JOURNAL_PHYSICS_LECTURE_NOTES:
            self.structure = INDIVIDUAL_PUBLCATIONS
        else:
            self.structure = ISSUES_AND_VOLUMES

    class Meta:
        model = Journal
        django_get_or_create = ('name',)


class VolumeFactory(factory.django.DjangoModelFactory):
    in_journal = factory.SubFactory(JournalFactory)
    number = 9999
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        self.number = self.in_journal.volumes.count()
        self.doi_label = self.in_journal.doi_label + '.' + str(self.number)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        self.start_date = Faker().date_time_between(start_date="-3y", end_date="now",
                                                    tzinfo=pytz.UTC)
        self.until_date = self.start_date + datetime.timedelta(weeks=26)

    class Meta:
        model = Volume
        django_get_or_create = ('in_journal', 'number')


class IssueFactory(factory.django.DjangoModelFactory):
    in_volume = factory.Iterator(Volume.objects.all())
    number = 9999
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        self.number = self.in_volume.issues.count()
        self.doi_label = self.in_volume.doi_label + '.' + str(self.number)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        self.start_date = Faker().date_time_between(start_date=self.in_volume.start_date,
                                                    end_date=self.in_volume.until_date,
                                                    tzinfo=pytz.UTC)
        self.until_date = self.start_date + datetime.timedelta(weeks=4)

    class Meta:
        model = Issue
        django_get_or_create = ('in_volume', 'number')


class PublicationFactory(factory.django.DjangoModelFactory):
    accepted_submission = factory.SubFactory(PublishedSubmissionFactory)
    paper_nr = 9999
    pdf_file = factory.Faker('file_name', extension='pdf')
    status = PUBLICATION_PUBLISHED
    submission_date = factory.Faker('date_this_year')
    acceptance_date = factory.Faker('date_this_year')
    publication_date = factory.Faker('date_this_year')
    doi_label = factory.Faker('md5')

    @factory.post_generation
    def doi(self, create, extracted, **kwargs):
        journal = Journal.objects.order_by('?').first()
        if journal.has_issues:
            self.in_issue = Issue.objects.order_by('?').first()
            paper_nr = self.in_issue.publications.count()
        else:
            self.in_journal = journal
            paper_nr = self.in_journal.publications.count()

        self.paper_nr = paper_nr
        if self.in_issue:
            self.doi_label = self.in_issue.doi_label + '.' + str(paper_nr).rjust(3, '0')
        else:
            self.doi_label = self.in_journal.doi_label + '.' + str(paper_nr)

    @factory.post_generation
    def submission_data(self, create, extracted, **kwargs):
        # Content
        self.discipline = self.accepted_submission.discipline
        self.domain = self.accepted_submission.domain
        self.subject_area = self.accepted_submission.subject_area
        self.title = self.accepted_submission.title
        self.abstract = self.accepted_submission.abstract

        # Dates
        self.submission_date = self.accepted_submission.latest_activity
        self.acceptance_date = self.accepted_submission.latest_activity
        self.publication_date = self.accepted_submission.latest_activity
        self.latest_activity = self.accepted_submission.latest_activity

        # Authors
        self.author_list = self.accepted_submission.author_list

        if not create:
            return

        # self.authors_registered.add(*self.accepted_submission.authors.all())
        for author in self.accepted_submission.authors.all():
            self.authors.create(publication=self, contributor=author)
        self.authors_claims.add(*self.accepted_submission.authors_claims.all())
        self.authors_false_claims.add(*self.accepted_submission.authors_false_claims.all())

    class Meta:
        model = Publication
        django_get_or_create = ('accepted_submission', )
