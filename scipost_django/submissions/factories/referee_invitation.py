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

    date_invited = factory.SelfAttribute("submission.latest_activity")
    date_last_reminded = factory.SelfAttribute("submission.latest_activity")
    intended_delivery_date = LazyAwareDateOffset("date_invited", "+30d")
    invited_by = factory.SelfAttribute("submission.editor_in_charge")

    nr_reminders = factory.Faker("random_int", min=0, max=3)
    invitation_key = factory.Faker("md5")


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    registered = True
    accepted = True
    date_responded = LazyAwareDateOffset("date_invited", "+1y")

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import VettedReportFactory

            VettedReportFactory(
                submission=self.submission, author=self.referee.contributor
            )


class FulfilledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = True


class CancelledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = False
    cancelled = True
