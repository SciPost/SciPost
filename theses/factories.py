import factory

from common.helpers.factories import FormFactory
from scipost.factories import ContributorFactory

from .models import ThesisLink
from .forms import VetThesisLinkForm
from .constants import MASTER_THESIS


class ThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ThesisLink

    requested_by = factory.SubFactory(ContributorFactory)
    type = MASTER_THESIS
    title = factory.Faker('bs')
    pub_link = factory.Faker('uri')
    author = factory.Faker('name')
    supervisor = factory.Faker('name')
    institution = factory.Faker('company')
    defense_date = factory.Faker('date')
    abstract = factory.Faker('text')
    domain = 'ET'


class VettedThesisLinkFactory(ThesisLinkFactory):
    vetted_by = factory.SubFactory(ContributorFactory)
    vetted = True


class VetThesisLinkFormFactory(FormFactory):
    class Meta:
        model = VetThesisLinkForm

    action_option = VetThesisLinkForm.ACCEPT
