__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import random

import factory
from colleges.factories import FellowshipFactory
from common.faker import LazyAwareDateOffset

from journals.factories import JournalIssueFactory
from proceedings.models import Proceedings


class ProceedingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Proceedings

    issue = factory.SubFactory(JournalIssueFactory)
    minimum_referees = 2
    event_name = factory.Faker("company")
    event_suffix = factory.Faker("company_suffix")
    event_description = factory.Faker("paragraph")
    event_start_date = factory.Faker("date_this_decade")
    event_end_date = LazyAwareDateOffset("event_start_date", "+1y")

    logo = factory.django.ImageField()
    picture = factory.django.ImageField()
    picture_credit = factory.Faker("sentence")
    cover_image = factory.django.ImageField()

    submissions_open = factory.Faker("date_this_decade")
    submissions_close = LazyAwareDateOffset("submissions_open", "+1y")
    submissions_deadline = LazyAwareDateOffset("submissions_close", "+14d")

    preface_title = factory.Faker("sentence")
    preface_text = factory.Faker("paragraph")

    template_latex_tgz = factory.django.FileField()
    # lead_fellow = factory.SubFactory("colleges.factories.SeniorFellowshipFactory")

    @factory.post_generation
    def fellowships(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for fellowship in extracted:
                self.fellowships.add(fellowship)
        else:
            self.fellowships.add(
                *FellowshipFactory.create_batch(
                    random.randint(1, 5),
                    college=self.issue.in_journal.college,
                )
            )
