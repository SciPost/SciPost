import factory
import random
import string

from scipost.factories import ContributorFactory

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
    arxiv_identifier_wo_vn_nr = factory.LazyAttribute(lambda obj: obj.arxiv_identifier_w_vn_nr[0:-2])
    domain = 'E'


class EICassignedSubmissionFactory(SubmissionFactory):
    status = 'EICassigned'
    editor_in_charge = factory.SubFactory(ContributorFactory)



def random_arxiv_identifier_with_version_number():
    return random_arxiv_identifier_without_version_number() + "v0"

def random_arxiv_identifier_without_version_number():
    return random_digits(4) + "." + random_digits(5)

def random_digits(n):
    return "".join(random.choice(string.digits) for _ in range(n))
