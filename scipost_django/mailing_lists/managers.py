__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from .constants import MAIL_LIST_STATUS_ACTIVE


class MailListManager(models.Manager):
    def active(self):
        """
        Return Lists active in the Mailchimp account.

        To be used on Admin pages.
        """
        return self.filter(status=MAIL_LIST_STATUS_ACTIVE)

    def open_to_subscribe(self, contributor):
        """
        Return Lists active in the Mailchimp account and open for
        subscription for Contributors in the settings page.


        """
        return self.filter(
            status=MAIL_LIST_STATUS_ACTIVE,
            open_for_subscription=True,
            allowed_groups__in=contributor.user.groups.all(),
        )
