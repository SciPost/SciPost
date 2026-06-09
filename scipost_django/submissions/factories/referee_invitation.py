__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.faker import LazyAwareDateOffset

from ..models import RefereeInvitation


class RefereeInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RefereeInvitation
        exclude = ("contributor",)
        django_get_or_create = ("submission", "referee")

    class Params:
        registered = factory.Trait(
            contributor=factory.SubFactory("scipost.factories.ContributorFactory"),
            referee=factory.SelfAttribute("contributor.profile"),
        )

    referee = factory.SubFactory("profiles.factories.ProfileFactory")

    email_address = factory.SelfAttribute("referee.email")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")

    date_invited = LazyAwareDateOffset("submission.eic_first_assigned_date", "+3d")
    date_last_reminded = factory.SelfAttribute("date_invited")
    intended_delivery_date = LazyAwareDateOffset("date_invited", "+30d")
    invited_by = factory.SelfAttribute("submission.editor_in_charge")

    nr_reminders = factory.Faker("random_int", min=0, max=3)
    invitation_key = factory.Faker("md5")


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    registered = True
    accepted = True
    date_responded = LazyAwareDateOffset("date_invited", "+15d")
    intended_delivery_date = LazyAwareDateOffset("date_responded", "+30d")


class FulfilledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = True

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if not create:
            return

        fuzzed_delay = fake.time_delta("-10d") + fake.time_delta("+5d")
        date_submitted = self.intended_delivery_date + fuzzed_delay

        if extracted:
            extracted.submission = self.submission
            extracted.author = self.referee.contributor
            extracted.date_submitted = date_submitted
            extracted.save()

        from submissions.factories import VettedReportFactory

        # The report is usually submitted earlier than,
        # but also occasionally later than the intended delivery date
        VettedReportFactory(
            submission=self.submission,
            author=self.referee.contributor,
            date_submitted=date_submitted,
            invited=True,
            **kwargs,
        )


class CancelledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = False
    cancelled = True
