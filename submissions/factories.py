import factory
import pytz

from django.utils import timezone

from scipost.models import Contributor
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_without_version_number, random_scipost_journal

from .constants import STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_RESUBMISSION_INCOMING,\
                       STATUS_PUBLISHED, SUBMISSION_TYPE, STATUS_RESUBMITTED
from .models import Submission

from faker import Faker


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    author_list = factory.Faker('name')
    submitted_by = Contributor.objects.first()
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
    submission_type = factory.Iterator(SUBMISSION_TYPE, getter=lambda c: c[0])
    is_current = True

    @factory.post_generation
    def fill_arxiv_fields(self, create, extracted, **kwargs):
        '''Fill empty arxiv fields.'''
        self.arxiv_link = 'https://arxiv.org/abs/%s' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_identifier_w_vn_nr = '%sv1' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_vn_nr = 1

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        contributors = list(Contributor.objects.order_by('?')[:4])

        # Auto-add the submitter as an author
        self.submitted_by = contributors.pop()

        if not create:
            return
        self.authors.add(self.submitted_by)

        # Add three random authors
        for contrib in contributors:
            self.authors.add(contrib)
            self.author_list += ', %s %s' % (contrib.user.first_name, contrib.user.last_name)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        timezone.now()
        if kwargs.get('submission', False):
            self.submission_date = kwargs['submission']
            self.cycle.update_deadline()
            return
        self.submission_date = Faker().date_time_between(start_date="-3y", end_date="now",
                                                         tzinfo=pytz.UTC).date()
        self.latest_activity = Faker().date_time_between(start_date=self.submission_date,
                                                         end_date="now", tzinfo=pytz.UTC)
        self.cycle.update_deadline()


class UnassignedSubmissionFactory(SubmissionFactory):
    '''This Submission is a 'new request' by a Contributor for its Submission.'''
    status = STATUS_UNASSIGNED


class EICassignedSubmissionFactory(SubmissionFactory):
    status = STATUS_EIC_ASSIGNED
    open_for_commenting = True
    open_for_reporting = True

    @factory.post_generation
    def eic(self, create, extracted, **kwargs):
        '''Assign an EIC to submission.'''
        author_ids = list(self.authors.values_list('id', flat=True))
        self.editor_in_charge = (Contributor.objects.order_by('?')
                                            .exclude(pk=self.submitted_by.pk)
                                            .exclude(pk__in=author_ids).first())


class ResubmittedSubmissionFactory(SubmissionFactory):
    '''This Submission is a `resubmitted` version.'''
    status = STATUS_RESUBMITTED
    open_for_commenting = False
    open_for_reporting = False
    is_current = False
    is_resubmission = False


class ResubmissionFactory(SubmissionFactory):
    """
    This Submission is a newer version of a Submission which is
    already known by the SciPost database.
    """
    status = STATUS_RESUBMISSION_INCOMING
    open_for_commenting = True
    open_for_reporting = True
    is_resubmission = True

    @factory.post_generation
    def fill_arxiv_fields(self, create, extracted, **kwargs):
        '''Fill empty arxiv fields.'''
        self.arxiv_link = 'https://arxiv.org/abs/%s' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_identifier_w_vn_nr = '%sv2' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_vn_nr = 2

    @factory.post_generation
    def eic(self, create, extracted, **kwargs):
        '''Assign an EIC to submission.'''
        author_ids = list(self.authors.values_list('id', flat=True))
        self.editor_in_charge = (Contributor.objects.order_by('?')
                                            .exclude(pk=self.submitted_by.pk)
                                            .exclude(pk__in=author_ids).first())

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
        """Overwrite the parent `dates` method to skip the update_deadline call."""
        timezone.now()
        if kwargs.get('submission', False):
            self.submission_date = kwargs['submission']
            return
        self.submission_date = Faker().date_time_between(start_date="-3y", end_date="now",
                                                         tzinfo=pytz.UTC).date()
        self.latest_activity = Faker().date_time_between(start_date=self.submission_date,
                                                         end_date="now", tzinfo=pytz.UTC)


class PublishedSubmissionFactory(SubmissionFactory):
    status = STATUS_PUBLISHED
    open_for_commenting = False
    open_for_reporting = False
