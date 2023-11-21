__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from ..models.preprint_server import PreprintServer


class PreprintServerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PreprintServer

    name = factory.Faker("sentence")
    url = factory.Faker("url")
    served_by = None

    @factory.post_generation
    def acad_fields(self, create, extracted, **kwargs):
        if create:
            return
        if extracted:
            for acad_field in extracted:
                self.acad_fields.add(acad_field)
        else:
            self.acad_fields.add(
                factory.SubFactory("ontology.factories.AcademicFieldFactory")
            )

    @classmethod
    def arxiv(cls):
        return cls(name="arXiv", url="https://arxiv.org/")
