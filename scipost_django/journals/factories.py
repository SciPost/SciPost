__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import random
from string import ascii_lowercase

import factory
import pytz
from common.helpers import (
    random_digits,
    random_external_doi,
    random_external_journal_abbrev,
)
from faker import Faker
from journals.constants import (
    ISSUES_AND_VOLUMES,
    ISSUES_ONLY,
    JOURNAL_STRUCTURE,
    PUBLICATION_PUBLISHED,
)

from .models import Issue, Journal, Publication, Reference, Volume


class ReferenceFactory(factory.django.DjangoModelFactory):
    reference_number = factory.LazyAttribute(
        lambda o: o.publication.references.count() + 1
    )
    identifier = factory.lazy_attribute(lambda n: random_external_doi())
    link = factory.Faker("uri")

    class Meta:
        model = Reference

    @factory.lazy_attribute
    def citation(self):
        faker = Faker()
        return "<em>{}</em> {} <b>{}</b>, {} ({})".format(
            faker.sentence(),
            random_external_journal_abbrev(),
            random.randint(1, 100),
            random.randint(1, 100),
            faker.year(),
        )


class JournalFactory(factory.django.DjangoModelFactory):
    college = factory.SubFactory("colleges.factories.CollegeFactory")
    name = factory.Sequence(lambda n: "Fake Journal %s" % ascii_lowercase[n])
    doi_label = factory.Sequence(lambda n: "SciPost%s" % ascii_lowercase[n])
    issn = factory.lazy_attribute(lambda n: random_digits(8))
    structure = factory.Iterator(JOURNAL_STRUCTURE, getter=lambda c: c[0])

    class Meta:
        model = Journal
        django_get_or_create = ("name",)

    @classmethod
    def SciPostPhysics(cls):
        return cls(
            name="SciPost Physics",
            doi_label="SciPostPhys",
            structure=ISSUES_AND_VOLUMES,
        )

    @classmethod
    def SciPostPhysicsProc(cls):
        return cls(
            name="SciPost Physics Proceedings",
            doi_label="SciPostPhysProc",
            structure=ISSUES_ONLY,
        )


class VolumeFactory(factory.django.DjangoModelFactory):
    in_journal = factory.SubFactory(JournalFactory)
    doi_label = factory.lazy_attribute(
        lambda o: "%s.%i" % (o.in_journal.doi_label, o.number)
    )
    number = factory.lazy_attribute(lambda o: o.in_journal.volumes.count() + 1)
    start_date = factory.Faker("date_time_this_decade")
    until_date = factory.lazy_attribute(
        lambda o: o.start_date + datetime.timedelta(weeks=26)
    )

    class Meta:
        model = Volume
        django_get_or_create = ("in_journal", "number")


class IssueFactory(factory.django.DjangoModelFactory):
    in_volume = factory.SubFactory(VolumeFactory)
    number = factory.LazyAttribute(lambda o: o.in_volume.issues.count() + 1)
    doi_label = factory.LazyAttribute(
        lambda o: "%s.%i" % (o.in_volume.doi_label, o.number)
    )

    start_date = factory.LazyAttribute(
        lambda o: Faker().date_time_between(
            start_date=o.in_volume.start_date,
            end_date=o.in_volume.until_date,
            tzinfo=pytz.UTC,
        )
    )
    until_date = factory.LazyAttribute(
        lambda o: o.start_date + datetime.timedelta(weeks=4)
    )

    class Meta:
        model = Issue
        django_get_or_create = ("in_volume", "number")


class PublicationFactory(factory.django.DjangoModelFactory):
    accepted_submission = factory.SubFactory(
        "submissions.factories.PublishedSubmissionFactory", generate_publication=False
    )
    paper_nr = 9999
    pdf_file = factory.Faker("file_name", extension="pdf")
    status = PUBLICATION_PUBLISHED
    submission_date = factory.Faker("date_this_year")
    acceptance_date = factory.Faker("date_this_year")
    publication_date = factory.Faker("date_this_year")

    acad_field = factory.SelfAttribute("accepted_submission.acad_field")

    title = factory.SelfAttribute("accepted_submission.title")
    abstract = factory.SelfAttribute("accepted_submission.abstract")

    # Dates
    submission_date = factory.LazyAttribute(
        lambda o: o.accepted_submission.submission_date
    )
    acceptance_date = factory.LazyAttribute(
        lambda o: o.accepted_submission.latest_activity
    )
    publication_date = factory.LazyAttribute(
        lambda o: o.accepted_submission.latest_activity
    )
    latest_activity = factory.LazyAttribute(
        lambda o: o.accepted_submission.latest_activity
    )

    # Authors
    author_list = factory.LazyAttribute(lambda o: o.accepted_submission.author_list)

    class Meta:
        model = Publication
        django_get_or_create = ("accepted_submission",)

    class Params:
        journal = None

    @factory.lazy_attribute
    def in_issue(self):
        # Make sure Issues, Journals and doi are correct.
        if self.journal:
            journal = Journal.objects.get(doi_label=self.journal)
        else:
            journal = Journal.objects.order_by("?").first()

        if journal.has_issues:
            return Issue.objects.for_journal(journal.name).order_by("?").first()
        return None

    @factory.lazy_attribute
    def in_journal(self):
        # Make sure Issues, Journals and doi are correct.
        if self.journal:
            journal = Journal.objects.get(doi_label=self.journal)
        elif not self.in_issue:
            journal = (
                Journal.objects.has_individual_publications().order_by("?").first()
            )
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

    @factory.post_generation
    def specialties(self, create, extracted, **kwargs):
        if not create:
            return
        self.specialties.add(*self.accepted_submission.specialties.all())

    @factory.post_generation
    def approaches(self, create, extracted, **kwargs):
        if not create:
            return
        self.approaches = self.accepted_submission.approaches

    @factory.lazy_attribute
    def doi_label(self):
        if self.in_issue:
            return self.in_issue.doi_label + "." + str(self.paper_nr).rjust(3, "0")
        elif self.in_journal:
            return "%s.%i" % (self.in_journal.doi_label, self.paper_nr)

    @factory.post_generation
    def generate_publication(self, create, extracted, **kwargs):
        if create and extracted is not False:
            return

        from journals.factories import PublicationFactory

        factory.RelatedFactory(
            PublicationFactory,
            "accepted_submission",
            title=self.title,
            author_list=self.author_list,
        )

    @factory.post_generation
    def author_relations(self, create, extracted, **kwargs):
        if not create:
            return

        # Append references
        for i in range(5):
            ReferenceFactory(publication=self)

        # Copy author data from Submission
        # for author in self.accepted_submission.authors.all():
        #     self.authors.create(publication=self, profile=author)
        # self.authors_claims.add(*self.accepted_submission.authors_claims.all())
        # self.authors_false_claims.add(*self.accepted_submission.authors_false_claims.all())
