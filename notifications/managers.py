__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class NotificationQuerySet(models.query.QuerySet):

    def unsent(self):
        return self.filter(emailed=False)

    def sent(self):
        return self.filter(emailed=True)

    def unread(self):
        """Return only unread items in the current queryset"""
        return self.filter(unread=True)

    def pseudo_unread(self):
        """Return only unread items in the current queryset"""
        return self.filter(pseudo_unread=True)

    def read(self):
        """Return only read items in the current queryset"""
        return self.filter(unread=False)

    def mark_all_as_read(self, recipient=None):
        """Mark as read any unread messages in the current queryset."""
        # We want to filter out read ones, as later we will store
        # the time they were marked as read.
        qs = self.unread()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(unread=False)

    def mark_all_as_pseudo_read(self, recipient=None):
        """Mark as read any unread messages in the current queryset."""
        # We want to filter out read ones, as later we will store
        # the time they were marked as read.
        qs = self.pseudo_unread()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(pseudo_unread=False)

    def mark_all_as_unread(self, recipient=None):
        """Mark as unread any read messages in the current queryset."""
        qs = self.read()

        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(unread=True)

    def deleted(self):
        """Return only deleted items in the current queryset"""
        raise DeprecationWarning
        return self.filter(deleted=True)

    def active(self):
        """Return only active(un-deleted) items in the current queryset"""
        raise DeprecationWarning
        return self.filter(deleted=False)

    def mark_all_as_deleted(self, recipient=None):
        """Mark current queryset as deleted."""
        raise DeprecationWarning
        qs = self.active()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(deleted=True)

    def mark_all_as_active(self, recipient=None):
        """Mark current queryset as active(un-deleted)."""
        raise DeprecationWarning
        qs = self.deleted()
        if recipient:
            qs = qs.filter(recipient=recipient)

        return qs.update(deleted=False)

    def mark_as_unsent(self, recipient=None):
        qs = self.sent()
        if recipient:
            qs = self.filter(recipient=recipient)
        return qs.update(emailed=False)

    def mark_as_sent(self, recipient=None):
        qs = self.unsent()
        if recipient:
            qs = self.filter(recipient=recipient)
        return qs.update(emailed=True)
