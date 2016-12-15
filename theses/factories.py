import factory
from .models import ThesisLink
from scipost.factories import ContributorFactory


class ThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ThesisLink

    requested_by = factory.SubFactory(ContributorFactory)
    type = ThesisLink.MASTER_THESIS
    title = factory.Sequence(lambda n: "thesis {0}".format(n))
    pub_link = factory.Faker('uri')
    author = factory.Faker('name')
    supervisor = factory.Faker('name')
    institution = factory.Faker('company')
    defense_date = factory.Faker('date_time_this_century')
    abstract = factory.Faker('text')
