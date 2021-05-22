__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.helpers.factories import FormFactory
from ontology.models import AcademicField, Specialty
from scipost.constants import SCIPOST_APPROACHES
from scipost.models import Contributor

from .models import ThesisLink
from .forms import VetThesisLinkForm
from .constants import THESIS_TYPES


class BaseThesisLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ThesisLink
        abstract = True

    requested_by = factory.SubFactory('scipost.factories.ContributorFactory')
    vetted_by = factory.SubFactory('scipost.factories.ContributorFactory')
    vetted = True

    type = factory.Iterator(THESIS_TYPES, getter=lambda c: c[0])
    acad_field = factory.SubFactory('ontology.factories.AcademicFieldFactory')
    approaches = factory.Iterator(SCIPOST_APPROACHES, getter=lambda c: [c[0],])
    title = factory.Faker('sentence')
    pub_link = factory.Faker('uri')
    author = factory.Faker('name')
    supervisor = factory.Faker('name')
    institution = factory.Faker('company')
    defense_date = factory.Faker('date_this_decade')
    abstract = factory.Faker('paragraph')

    @classmethod
    def create(cls, **kwargs):
        if AcademicField.objects.count() < 5:
            from ontology.factories import AcademicFieldactory
            AcademicFieldFactory.create_batch(5)
        if Specialty.objects.count() < 5:
            from ontology.factories import SpecialtyFactory
            SpecialtyFactory.create_batch(5)
        return super().create(**kwargs)

    @factory.post_generation
    def add_specialties(self, create, extracted, **kwargs):
        if create:
            self.specialties.set(Specialty.objects.order_by('?')[:3])

    @factory.post_generation
    def author_as_cont(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for contributor in extracted:
                self.author_as_cont.add(contributor)
        elif factory.Faker('boolean'):
            contributor = Contributor.objects.order_by('?').first()
            self.author_as_cont.add(contributor)


class ThesisLinkFactory(BaseThesisLinkFactory):
    pass


class VetThesisLinkFormFactory(FormFactory):
    class Meta:
        model = VetThesisLinkForm

    action_option = VetThesisLinkForm.ACCEPT
