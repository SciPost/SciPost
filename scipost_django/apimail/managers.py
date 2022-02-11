__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models


class DomainQuerySet(models.QuerySet):
    def active(self):
        from apimail.models import Domain

        return self.filter(status=Domain.STATUS_ACTIVE)


class EmailAccountAccessQuerySet(models.QuerySet):
    def current(self):
        today = datetime.date.today()
        return self.filter(date_from__lt=today, date_until__gt=today)

    def can_send(self):
        return self.filter(rights="CRUD")


class ComposedMessageQuerySet(models.QuerySet):
    """
    All ComposedMessage querysets are always filtered for the user.
    """

    def filter_for_user(self, user):
        return self.filter(author=user)

    def ready(self):
        return self.filter(status="ready")


class StoredMessageQuerySet(models.QuerySet):
    """
    All StoredMessage querysets are always filtered for the user.
    """

    def filter_for_user(self, user, email):
        """
        Either su or staff, or user's email account accesses overlap with sender/recipients.
        """
        if not user.is_authenticated:
            return self.none()
        elif (user.is_superuser or user.is_staff) and email is None:
            return self

        # Filter based on account accesses
        if user.email_account_accesses.filter(account__email=email).exists():
            queryfilter = models.Q()
            for access in user.email_account_accesses.filter(account__email=email):
                queryfilter = queryfilter | (
                    (
                        models.Q(data__sender__icontains=access.account.email)
                        | models.Q(data__recipients__icontains=access.account.email)
                    )
                    & models.Q(datetimestamp__gt=access.date_from)
                    & models.Q(datetimestamp__lt=access.date_until)
                )
            return self.filter(queryfilter)
        return self.none()

    def in_thread_of_uuid(self, thread_of_uuid):
        """
        Filters for messages in the thread of message with given uuid.

        Identify email thread using data['References'] or data['Message-Id'].
        Since Django ORM does not support hyphenated lookups, use raw SQL.
        First find the message at the root of the thread, which is the message
        with Message-Id first in the list of the message with uuid `thread_of_uuid`
        """
        try:
            reference_message = self.model.objects.get(uuid=thread_of_uuid)
        except self.model.DoesNotExist:
            return self.none()

        # First try the RFC 2822 References MIME header:
        head_id = None
        try:
            head_id = reference_message.data["References"].split()[0]
        except KeyError:
            # Then try the RFC 2822 In-Reply-To
            try:
                head_id = reference_message.data["In-Reply-To"].split()[0]
            except KeyError:
                # This message is head of the thread as far as can be guessed
                head_id = reference_message.data["Message-Id"]

        if head_id:
            thread_query_raw = (
                "SELECT apimail_storedmessage.id FROM apimail_storedmessage "
                "WHERE UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "OR UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "ORDER BY apimail_storedmessage.datetimestamp DESC;"
            )
            sm_ids = [
                sm.id
                for sm in self.model.objects.raw(
                    thread_query_raw,
                    [
                        "Message-Id",
                        "%%%s%%" % head_id,
                        "References",
                        "%%%s%%" % head_id,
                    ],
                )
            ]
            return self.filter(pk__in=sm_ids)

        # Otherwise message is already the head
        return self.filter(uuid=thread_of_uuid)
