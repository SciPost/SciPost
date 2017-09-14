from haystack import signals
from haystack.exceptions import NotHandled

from submissions.models import Submission


class AutoSearchIndexingProcessor(signals.RealtimeSignalProcessor):
    def prepare_submission_indexing(self, sender, submissions):
        """
        Given an individual model instance, determine which backends the
        update should be sent to & update the object on those backends.
        """
        try:
            using_backends = self.connection_router.for_write(instance=submissions[0])
        except IndexError:
            # No submissions given, stop processing here
            return None

        for instance in submissions:
            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index().get_index(sender)
                    index.remove_object(instance, using=using)
                except NotHandled:
                    # TODO: Maybe log it or let the exception bubble?
                    pass

    def handle_save(self, sender, instance, **kwargs):
        if isinstance(instance, Submission):
            # Submission have complex status handling, so a status change should lead to
            # more drastic reindexing.
            self.prepare_submission_indexing(sender, [instance])
            self.prepare_submission_indexing(sender, instance.other_versions)
        super().handle_save(sender, instance, **kwargs)
