import factory
import datetime
import pytz

from django.utils import timezone

from scipost.factories import ContributorFactory
from scipost.models import Contributor
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_without_version_number, random_scipost_journal

from .constants import STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_RESUBMISSION_INCOMING,\
                       STATUS_PUBLISHED
from .models import Submission

from faker import Faker


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    author_list = factory.Faker('name')
    submitted_by = factory.SubFactory(ContributorFactory)
    submitted_to_journal = factory.Sequence(lambda n: random_scipost_journal())
    title = factory.lazy_attribute(lambda x: Faker().sentence())
    abstract = factory.lazy_attribute(lambda x: Faker().paragraph())
    arxiv_link = factory.Faker('uri')
    arxiv_identifier_wo_vn_nr = factory.Sequence(
                                    lambda n: random_arxiv_identifier_without_version_number())
    domain = SCIPOST_JOURNALS_DOMAINS[0][0]
    abstract = Faker().paragraph()
    author_comments = Faker().paragraph()
    remarks_for_editors = Faker().paragraph()
    submission_type = 'Letter'

    @factory.post_generation
    def fill_arxiv_fields(self, create, extracted, **kwargs):
        '''Fill empty arxiv fields.'''
        self.arxiv_link = 'https://arxiv.org/abs/%s' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_identifier_w_vn_nr = '%sv1' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_vn_nr = 1

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        contributors = list(Contributor.objects.order_by('?')
                            .exclude(pk=self.submitted_by.pk).all()[:4])
        if not create:
            return
        self.editor_in_charge = contributors.pop()
        for contrib in contributors:
            self.authors.add(contrib)
            self.author_list += ', %s %s' % (contrib.user.first_name, contrib.user.last_name)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        timezone.now()
        self.submission_date = Faker().date_time_between(start_date="-3y", end_date="now",
                                                         tzinfo=pytz.UTC)
        self.latest_activity = Faker().date_time_between(start_date=self.submission_date,
                                                         end_date="now", tzinfo=pytz.UTC)


class EICassignedSubmissionFactory(SubmissionFactory):
    status = STATUS_EIC_ASSIGNED
    open_for_commenting = True
    open_for_reporting = True

    @factory.post_generation
    def report_dates(self, create, extracted, **kwargs):
        self.reporting_deadline = self.latest_activity + datetime.timedelta(weeks=2)


class UnassignedSubmissionFactory(SubmissionFactory):
    status = STATUS_UNASSIGNED


class ResubmittedScreeningSubmissionFactory(SubmissionFactory):
    status = STATUS_RESUBMISSION_INCOMING


class PublishedSubmissionFactory(SubmissionFactory):
    status = STATUS_PUBLISHED
    open_for_commenting = False
    open_for_reporting = False
    is_current = True
