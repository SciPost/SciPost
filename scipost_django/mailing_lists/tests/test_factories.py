__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.test import TestCase

from profiles.factories import ProfileEmailFactory
from scipost.factories import ContributorFactory
from ..factories import *


class TestMailingListFactory(TestCase):
    def test_can_create_mailing_lists(self):
        mailing_list = MailingListFactory()
        self.assertIsNotNone(mailing_list)

    def test_can_subscribe_contributor(self):
        profile_email = ProfileEmailFactory(primary=True)
        contributor = ContributorFactory.from_profile(profile_email.profile)
        mailing_list = MailingListFactory()
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 1)
        self.assertEquals(mailing_list.email_list, [profile_email.email])

    def test_can_unsubscribe_contributor(self):
        profile_email = ProfileEmailFactory(primary=True)
        contributor = ContributorFactory.from_profile(profile_email.profile)
        mailing_list = MailingListFactory()

        mailing_list.add_eligible_subscriber(contributor)
        mailing_list.unsubscribe(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 0)
        self.assertEquals(mailing_list.email_list, [])

    def test_does_not_automatically_subscribe_if_opt_in(self):
        profile_email = ProfileEmailFactory(primary=True)
        contributor = ContributorFactory.from_profile(profile_email.profile)
        mailing_list = MailingListFactory(is_opt_in=True)
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEqual(mailing_list.eligible_subscribers.count(), 1)
        self.assertEqual(mailing_list.subscribed.count(), 0)
        self.assertEquals(mailing_list.email_list, [])

    def test_does_not_include_nonprimary_emails(self):
        profile_email = ProfileEmailFactory(primary=False)
        profile_email_primary = ProfileEmailFactory(
            primary=True, profile=profile_email.profile
        )
        contributor = ContributorFactory.from_profile(profile_email.profile)
        mailing_list = MailingListFactory()
        mailing_list.add_eligible_subscriber(contributor)

        self.assertEquals(mailing_list.email_list, [profile_email_primary.email])
