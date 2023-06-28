__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory
import pytz
import random

from faker import Faker

from scipost.models import Contributor

from submissions.models import RefereeInvitation


class RefereeInvitationFactory(factory.django.DjangoModelFactory):
    submission = factory.SubFactory("submissions.factories.SubmissionFactory")
    referee = factory.lazy_attribute(
        lambda o: Contributor.objects.exclude(id__in=o.submission.authors.all())
        .order_by("?")
        .first()
    )

    title = factory.lazy_attribute(lambda o: o.referee.profile.title)
    first_name = factory.lazy_attribute(lambda o: o.referee.user.first_name)
    last_name = factory.lazy_attribute(lambda o: o.referee.user.last_name)
    email_address = factory.lazy_attribute(lambda o: o.referee.user.email)
    date_invited = factory.lazy_attribute(lambda o: o.submission.latest_activity)
    nr_reminders = factory.lazy_attribute(lambda o: random.randint(0, 4))
    date_last_reminded = factory.lazy_attribute(lambda o: o.submission.latest_activity)

    invitation_key = factory.Faker("md5")
    invited_by = factory.lazy_attribute(lambda o: o.submission.editor_in_charge)

    class Meta:
        model = RefereeInvitation


class AcceptedRefereeInvitationFactory(RefereeInvitationFactory):
    accepted = True
    date_responded = factory.lazy_attribute(
        lambda o: Faker().date_time_between(
            start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC
        )
    )

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import VettedReportFactory

            VettedReportFactory(submission=self.submission, author=self.referee)


class FulfilledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = True
    date_responded = factory.lazy_attribute(
        lambda o: Faker().date_time_between(
            start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC
        )
    )

    @factory.post_generation
    def report(self, create, extracted, **kwargs):
        if create:
            from submissions.factories import VettedReportFactory

            VettedReportFactory(submission=self.submission, author=self.referee)


class CancelledRefereeInvitationFactory(AcceptedRefereeInvitationFactory):
    fulfilled = False
    cancelled = True
    date_responded = factory.lazy_attribute(
        lambda o: Faker().date_time_between(
            start_date=o.date_invited, end_date="now", tzinfo=pytz.UTC
        )
    )
