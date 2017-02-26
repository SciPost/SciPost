import factory

from scipost.factories import ContributorFactory
from common.helpers import random_arxiv_identifier_with_version_number

from .models import Submission


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    author_list = factory.Faker('name')
    submitted_by = factory.SubFactory(ContributorFactory)
    submitted_to_journal = 'SciPost Physics'
    title = factory.Faker('bs')
    abstract = factory.Faker('text')
    arxiv_link = factory.Faker('uri')
    arxiv_identifier_w_vn_nr = factory.Sequence(lambda n: random_arxiv_identifier_with_version_number())
    domain = 'E'


class EICassignedSubmissionFactory(SubmissionFactory):
    status = 'EICassigned'
    editor_in_charge = factory.SubFactory(ContributorFactory)
    open_for_commenting = True
