__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import datetime
import pytz
import random

from common.helpers import random_digits, random_external_doi, random_external_journal_abbrev
from journals.constants import JOURNAL_STRUCTURE, PUBLICATION_PUBLISHED
from submissions.factories import PublishedSubmissionFactory

from .models import Journal, Volume, Issue, Publication, Reference

from faker import Faker


class ReferenceFactory(factory.django.DjangoModelFactory):
    reference_number = factory.LazyAttribute(lambda o: o.publication.references.count() + 1)
    identifier = factory.lazy_attribute(lambda n: random_external_doi())
    link = factory.Faker('uri')

    class Meta:
        model = Reference

    @factory.lazy_attribute
    def citation(self):
        faker = Faker()
        return '<em>{}</em> {} <b>{}</b>, {} ({})'.format(
            faker.sentence(),
            random_external_journal_abbrev(),
            random.randint(1, 100),
            random.randint(1, 100),
            faker.year())


class JournalFactory(factory.django.DjangoModelFactory):
    college = factory.SubFactory('colleges.factories.CollegeFactory')
    name = 'Fake Journal'
    doi_label = 'SciPostFakeJournal'
    issn = factory.lazy_attribute(lambda n: random_digits(8))
    structure = factory.Iterator(JOURNAL_STRUCTURE, getter=lambda c: c[0])

    class Meta:
        model = Journal
        django_get_or_create = ('name',)


class VolumeFactory(factory.django.DjangoModelFactory):
    in_journal = factory.SubFactory(JournalFactory)
    doi_label = factory.lazy_attribute(lambda o: '%s.%i' % (o.in_journal.doi_label, o.number))
    number = factory.lazy_attribute(lambda o: o.in_journal.volumes.count() + 1)
    start_date = factory.Faker('date_time_this_decade')
    until_date = factory.lazy_attribute(lambda o: o.start_date + datetime.timedelta(weeks=26))

    class Meta:
        model = Volume
        django_get_or_create = ('in_journal', 'number')


class IssueFactory(factory.django.DjangoModelFactory):
    in_volume = factory.Iterator(Volume.objects.all())
    number = factory.LazyAttribute(lambda o: o.in_volume.issues.count() + 1)
    doi_label = factory.LazyAttribute(lambda o: '%s.%i' % (o.in_volume.doi_label, o.number))

    start_date = factory.LazyAttribute(lambda o: Faker().date_time_between(
        start_date=o.in_volume.start_date, end_date=o.in_volume.until_date, tzinfo=pytz.UTC))
    until_date = factory.LazyAttribute(lambda o: o.start_date + datetime.timedelta(weeks=4))

    class Meta:
        model = Issue
        django_get_or_create = ('in_volume', 'number')


class PublicationFactory(factory.django.DjangoModelFactory):
    accepted_submission = factory.SubFactory(
        PublishedSubmissionFactory, generate_publication=False)
    paper_nr = 9999
    pdf_file = factory.Faker('file_name', extension='pdf')
    status = PUBLICATION_PUBLISHED
    submission_date = factory.Faker('date_this_year')
    acceptance_date = factory.Faker('date_this_year')
    publication_date = factory.Faker('date_this_year')

    acad_field = factory.LazyAttribute(lambda o: o.accepted_submission.acad_field)
    specialties = factory.LazyAttribute(lambda o: o.accepted_submission.specialties)
    approaches = factory.LazyAttribute(lambda o: o.accepted_submission.approaches)
    title = factory.LazyAttribute(lambda o: o.accepted_submission.title)
    abstract = factory.LazyAttribute(lambda o: o.accepted_submission.abstract)

    # Dates
    submission_date = factory.LazyAttribute(lambda o: o.accepted_submission.submission_date)
    acceptance_date = factory.LazyAttribute(lambda o: o.accepted_submission.latest_activity)
    publication_date = factory.LazyAttribute(lambda o: o.accepted_submission.latest_activity)
    latest_activity = factory.LazyAttribute(lambda o: o.accepted_submission.latest_activity)

    # Authors
    author_list = factory.LazyAttribute(lambda o: o.accepted_submission.author_list)

    class Meta:
        model = Publication
        django_get_or_create = ('accepted_submission', )

    class Params:
        journal = None

    @factory.lazy_attribute
    def in_issue(self):
        # Make sure Issues, Journals and doi are correct.
        if self.journal:
            journal = Journal.objects.get(name=self.journal)
        else:
            journal = Journal.objects.order_by('?').first()

        if journal.has_issues:
            return Issue.objects.for_journal(journal.name).order_by('?').first()
        return None

    @factory.lazy_attribute
    def in_journal(self):
        # Make sure Issues, Journals and doi are correct.
        if self.journal:
            journal = Journal.objects.get(name=self.journal)
        elif not self.in_issue:
            journal = Journal.objects.has_individual_publications().order_by('?').first()
        else:
            return None

        if not journal.has_issues:
            # Keep this logic in case self.journal is set.
            return journal
        return None

    @factory.lazy_attribute
    def paper_nr(self):
        if self.in_issue:
            return self.in_issue.publications.count() + 1
        elif self.in_journal:
            return self.in_journal.publications.count() + 1

    @factory.lazy_attribute
    def doi_label(self):
        if self.in_issue:
            return self.in_issue.doi_label + '.' + str(self.paper_nr).rjust(3, '0')
        elif self.in_journal:
            return '%s.%i' % (self.in_journal.doi_label, self.paper_nr)

    @factory.post_generation
    def generate_publication(self, create, extracted, **kwargs):
        if create and extracted is not False:
            return

        from journals.factories import PublicationFactory
        factory.RelatedFactory(
            PublicationFactory, 'accepted_submission',
            title=self.title, author_list=self.author_list)

    @factory.post_generation
    def author_relations(self, create, extracted, **kwargs):
        if not create:
            return

        # Append references
        for i in range(5):
            ReferenceFactory(publication=self)

        # Copy author data from Submission
        for author in self.accepted_submission.authors.all():
            self.authors.create(publication=self, contributor=author)
        self.authors_claims.add(*self.accepted_submission.authors_claims.all())
        self.authors_false_claims.add(*self.accepted_submission.authors_false_claims.all())
