__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class StoredMessageQuerySet(models.QuerySet):
    """
    All StoredMessage querysets are always filtered for the user.
    """
    def filter_for_user(self, user):
        """
        Either su or staff, or user's email addresses overlap with sender/recipients.
        """
        if not user.is_authenticated:
            return self.none()
        elif user.is_superuser or user.is_admin:
            return self
        emails = [user.email,] if user.email else []
        if user.contributor:
            for pe in user.contributor.profile.emails.all():
                emails.append(pe.email)
        return self.filter_for_emails(emails=emails)

    def filter_for_emails(self, emails):
        """
        Ensure overlap of the emails in emails kwarg with those in sender or recipients.
        """
        emails_used = emails
        if not isinstance(emails, list):
            emails_used = [emails]
        emails_lower = [e.lower() for e in emails_used]
        return self.filter(
            models.Q(data__sender__in=emails_lower) |
            models.Q(data__recipients__in=emails_lower) | # if recipients is a single entry
            models.Q(data__recipients__overlap=emails_lower)) # if recipients is a list
