import factory

from scipost.factories import ContributorFactory
from journals.constants import SCIPOST_JOURNAL_PHYSICS
from common.helpers import random_arxiv_identifier_with_version_number

from .constants import STATUS_UNASSIGNED, STATUS_EIC_ASSIGNED, STATUS_RESUBMISSION_INCOMING
from .models import Submission


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    author_list = factory.Faker('name')
    submitted_by = factory.SubFactory(ContributorFactory)
    submitted_to_journal = SCIPOST_JOURNAL_PHYSICS
    title = factory.Faker('bs')
    abstract = factory.Faker('text')
    arxiv_link = factory.Faker('uri')
    arxiv_identifier_w_vn_nr = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number())
    domain = 'E'


class EICassignedSubmissionFactory(SubmissionFactory):
    status = STATUS_EIC_ASSIGNED
    editor_in_charge = factory.SubFactory(ContributorFactory)
    open_for_commenting = True


class UnassignedSubmissionFactory(SubmissionFactory):
    status = STATUS_UNASSIGNED


class ResubmittedScreeningSubmissionFactory(SubmissionFactory):
    status = STATUS_RESUBMISSION_INCOMING
    editor_in_charge = factory.SubFactory(ContributorFactory)
