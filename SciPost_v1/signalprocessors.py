__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from haystack import signals
from haystack.exceptions import NotHandled

from SciPost_v1.celery import app
from submissions.models import Submission


class AutoSearchIndexingProcessor(signals.RealtimeSignalProcessor):

    @app.task(bind=True, name='signalprocessors.remove_object_indexes',
              serializer='pickle')
    def remove_objects_indexes(self, sender, objects):
        """
        Given a set of `objects` model instances, remove them from the index as preparation
        for the new index.
        """
        try:
            using_backends = self.connection_router.for_write(instance=objects[0])
        except IndexError:
            # No submissions given, stop processing here
            return None

        for instance in objects:
            for using in using_backends:
                try:
                    index = self.connections[using].get_unified_index().get_index(sender)
                    index.remove_object(instance, using=using)
                except NotHandled:
                    # TODO: Maybe log it or let the exception bubble?
                    pass

    @app.task(bind=True, name='signalprocessors.update_instance_indexes',
              serializer='pickle')
    def update_instance_indexes(self, sender, instance):
        """
        Given an individual model instance, update its entire indexes.
        """
        try:
            using_backends = self.connection_router.for_write(instance=instance)
        except IndexError:
            # No valid instance given, stop processing here
            return None

        for using in using_backends:
            try:
                index = self.connections[using].get_unified_index().get_index(sender)
                index.update(using=using)
            except NotHandled:
                # TODO: Maybe log it or let the exception bubble?
                pass

    def handle_save(self, sender, instance, **kwargs):
        if isinstance(instance, Submission):
            # Submission have complex status handling, so a status change should lead to
            # more drastic reindexing.
            chain = (
                self.remove_objects_indexes.s(sender, instance.thread.public())
                |
                self.update_instance_indexes.s(sender, instance)
            )
            chain()

        else:
            # Objects such as Reports, Comments, Commentaries, etc. may get rejected. This
            # does not remove them from the index. Therefore, do a complete rebuild_index
            # action on that specific instance every time the index signal is triggered.
            chain = (
                self.remove_objects_indexes.s(sender, [instance])
                |
                self.update_instance_indexes.s(sender, instance)
            )
            chain()
