import factory
import pytz

from django.utils import timezone

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.models import Contributor
from journals.constants import SCIPOST_JOURNALS_DOMAINS
from common.helpers import random_arxiv_identifier_without_version_number, random_scipost_journal,\
    random_scipost_report_doi_label

from .constants import STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_RESUBMISSION_INCOMING,\
                       STATUS_PUBLISHED, SUBMISSION_TYPE, STATUS_RESUBMITTED, STATUS_VETTED,\
                       REFEREE_QUALIFICATION, RANKING_CHOICES, QUALITY_SPEC, REPORT_REC,\
                       REPORT_STATUSES, STATUS_UNVETTED, STATUS_DRAFT
from .models import Submission, Report, RefereeInvitation

from faker import Faker


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    author_list = factory.Faker('name')
    submitted_by = factory.Iterator(Contributor.objects.all())
    submission_type = factory.Iterator(SUBMISSION_TYPE, getter=lambda c: c[0])
    submitted_to_journal = factory.Sequence(lambda n: random_scipost_journal())
    title = factory.Faker('sentence')
    abstract = factory.Faker('paragraph', nb_sentences=10)
    arxiv_link = factory.Faker('uri')
    arxiv_identifier_wo_vn_nr = factory.Sequence(
        lambda n: random_arxiv_identifier_without_version_number())
    subject_area = factory.Iterator(SCIPOST_SUBJECT_AREAS[0][1], getter=lambda c: c[0])
    domain = factory.Iterator(SCIPOST_JOURNALS_DOMAINS, getter=lambda c: c[0])
    abstract = factory.Faker('paragraph')
    author_comments = factory.Faker('paragraph')
    remarks_for_editors = factory.Faker('paragraph')
    is_current = True

    submission_date = factory.Faker('date_this_decade')

    @factory.post_generation
    def fill_arxiv_fields(self, create, extracted, **kwargs):
        '''Fill empty arxiv fields.'''
        arxiv_vn_nr = kwargs.get('arxiv_vn_nr', 1)
        self.arxiv_link = 'https://arxiv.org/abs/%s' % self.arxiv_identifier_wo_vn_nr
        self.arxiv_identifier_w_vn_nr = '%sv%i' % (self.arxiv_identifier_wo_vn_nr, arxiv_vn_nr)
        self.arxiv_vn_nr = arxiv_vn_nr

    @factory.post_generation
    def contributors(self, create, extracted, **kwargs):
        contributors = list(Contributor.objects.order_by('?')[:4])

        # Auto-add the submitter as an author
        self.submitted_by = contributors.pop()
        self.author_list = ', '.join([
            '%s %s' % (c.user.first_name, c.user.last_name) for c in contributors])

        if not create:
            return
        self.authors.add(self.submitted_by)

        # Add three random authors
        for contrib in contributors:
            self.authors.add(contrib)

    @factory.post_generation
    def dates(self, create, extracted, **kwargs):
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

    @factory.post_generation
    def acceptance_date(self, create, extracted, **kwargs):
        self.latest_activity = Faker().date_time_between(start_date=self.submission_date,
                                                         end_date="now", tzinfo=pytz.UTC)


class ReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Report

    status = factory.Iterator(REPORT_STATUSES, getter=lambda c: c[0])
    submission = factory.Iterator(Submission.objects.all())
    date_submitted = factory.Faker('date_time_this_decade')
    vetted_by = factory.Iterator(Contributor.objects.all())
    author = factory.Iterator(Contributor.objects.all())
    qualification = factory.Iterator(REFEREE_QUALIFICATION, getter=lambda c: c[0])
    strengths = factory.Faker('paragraph')
    weaknesses = factory.Faker('paragraph')
    report = factory.Faker('paragraph')
    requested_changes = factory.Faker('paragraph')

    validity = factory.Iterator(RANKING_CHOICES, getter=lambda c: c[0])
    significance = factory.Iterator(RANKING_CHOICES, getter=lambda c: c[0])
    originality = factory.Iterator(RANKING_CHOICES, getter=lambda c: c[0])
    clarity = factory.Iterator(RANKING_CHOICES, getter=lambda c: c[0])
    formatting = factory.Iterator(QUALITY_SPEC, getter=lambda c: c[0])
    grammar = factory.Iterator(QUALITY_SPEC, getter=lambda c: c[0])
    recommendation = factory.Iterator(REPORT_REC, getter=lambda c: c[0])

    remarks_for_editors = factory.Faker('paragraph')
    flagged = factory.Faker('boolean', chance_of_getting_true=10)
    anonymous = factory.Faker('boolean', chance_of_getting_true=75)


class DraftReportFactory(ReportFactory):
    status = STATUS_DRAFT
    vetted_by = None


class UnVettedReportFactory(ReportFactory):
    status = STATUS_UNVETTED
    vetted_by = None


class VettedReportFactory(ReportFactory):
    status = STATUS_VETTED
    needs_doi = True
    doideposit_needs_updating = factory.Faker('boolean')
    doi_label = factory.lazy_attribute(lambda n: random_scipost_report_doi_label())
    pdf_report = factory.Faker('file_name', extension='pdf')


class RefereeInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RefereeInvitation

    submission = factory.SubFactory('submissions.factories.SubmissionFactory')
    referee = factory.Iterator(Contributor.objects.all())

    invitation_key = factory.Faker('md5')
    invited_by = factory.Iterator(Contributor.objects.all())

    @factory.post_generation
    def contributor_fields(self, create, extracted, **kwargs):
        self.title = self.referee.title
        self.first_name = self.referee.user.first_name
        self.last_name = self.referee.user.last_name
        self.email_address = self.referee.user.email


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    accepted = True
    date_responded = Faker().date_time_between(start_date="-1y", end_date="now", tzinfo=pytz.UTC)
