__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from common.faker import fake

from ..models import RefereeInvitation


class RefereeInvitationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RefereeInvitation
        exclude = ("profile_info",)
        django_get_or_create = ("submission", "profile")

    class Params:
        registered = factory.Trait(
            referee=factory.SubFactory("scipost.factories.ContributorFactory"),
            profile=None,
            profile_info=factory.SelfAttribute("referee.profile"),
        )

    referee = None
    profile = factory.SubFactory("profiles.factories.ProfileFactory")

    profile_info = factory.SelfAttribute("profile")
    title = factory.SelfAttribute("profile_info.title")
    first_name = factory.SelfAttribute("profile_info.first_name")
    last_name = factory.SelfAttribute("profile_info.last_name")
    email_address = factory.SelfAttribute("profile_info.email")

    submission = factory.SubFactory("submissions.factories.SubmissionFactory")

    date_invited = factory.SelfAttribute("submission.latest_activity")
    date_last_reminded = factory.SelfAttribute("submission.latest_activity")
    invited_by = factory.SelfAttribute("submission.editor_in_charge")

    nr_reminders = factory.Faker("random_int", min=0, max=3)
    invitation_key = factory.Faker("md5")


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    registered = True
    accepted = True
    date_responded = factory.LazyAttribute(
        lambda self: fake.aware.date_time_between(
            start_date=self.date_invited, end_date="+1y"
        )
    )

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import VettedReportFactory

            VettedReportFactory(submission=self.submission, author=self.referee)


class FulfilledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = True


class CancelledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = False
    cancelled = True
