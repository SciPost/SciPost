import factory

from scipost.factories import ContributorFactory

from .models import Submission


class SubmissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Submission

    submitted_by = factory.SubFactory(ContributorFactory)
    submitted_to_journal = 'SciPost Physics'
    title = factory.Faker('bs')
    abstract = factory.Faker('text')
    arxiv_link = factory.Faker('uri')


    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        # Add a single author if factory is invoked with strategy 'create'
        if not create:
            return
        else:
            self.authors.add(ContributorFactory())
