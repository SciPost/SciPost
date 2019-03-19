__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.models import ContentType

from haystack import signals
from haystack.exceptions import NotHandled

from SciPost_v1.celery import app
from notifications.models import Notification
from submissions.models import Submission


@app.task(name='signalprocessors.remove_object_indexes')
def remove_objects_indexes(processor_type_id, processor_id,
                           sender_type_id, object_type_id, object_id):
    """
    Given a set of `objects` model instances, remove them from the index as preparation
    for the new index.
    """
    processor_type = ContentType.objects.get_for_id(processor_type_id)
    processor = processor_type.get_object_for_this_type(pk=processor_id)
    sender = ContentType.objects.get_for_id(sender_type_id)
    object_type = ContentType.objects.get_for_id(object_type_id)
    instance = object_type.get_object_for_this_type(pk=object_id)

    if isinstance(instance, Submission):
        # Submission have complex status handling, so a status change should lead to
        # more drastic reindexing.
        ids_list = [k['id'] for k in list(instance.thread.public().values('id'))]
        objects = Submission.objects.filter(pk__in=ids_list)
    else:
        # Objects such as Reports, Comments, Commentaries, etc. may get rejected. This
        # does not remove them from the index. Therefore, do a complete rebuild_index
        # action on that specific instance every time the index signal is triggered.
        objects = [instance]

    try:
        using_backends = processor.connection_router.for_write(instance=objects[0])
    except IndexError:
        # No submissions given, stop processing here
        return None

    for instance in objects:
        for using in using_backends:
            try:
                index = processor.connections[using].get_unified_index().get_index(sender)
                index.remove_object(instance, using=using)
            except NotHandled:
                # TODO: Maybe log it or let the exception bubble?
                pass


@app.task(name='signalprocessors.update_instance_indexes')
def update_instance_indexes(processor_type_id, processor_id,
                            sender_type_id, object_type_id, object_id):
    """
    Given an individual model instance, update its entire indexes.
    """
    processor_type = ContentType.objects.get_for_id(processor_type_id)
    processor = processor_type.get_object_for_this_type(pk=processor_id)
    sender = ContentType.objects.get_for_id(sender_type_id)
    object_type = ContentType.objects.get_for_id(object_type_id)
    instance = object_type.get_object_for_this_type(pk=object_id)

    try:
        using_backends = processor.connection_router.for_write(instance=instance)
    except IndexError:
        # No valid instance given, stop processing here
        return None

    for using in using_backends:
        try:
            index = processor.connections[using].get_unified_index().get_index(sender)
            index.update(using=using)
        except NotHandled:
            # TODO: Maybe log it or let the exception bubble?
            pass


class AutoSearchIndexingProcessor(signals.RealtimeSignalProcessor):

    def handle_save(self, sender, instance, **kwargs):
        # if not isinstance(instance, Notification):
        #     processor_type_id = ContentType.objects.get_for_model(self).id
        #     sender_type_id = ContentType.objects.get_for_model(sender).id
        #     instance_type_id = ContentType.objects.get_for_model(instance).id
        #     chain = (
        #         remove_objects_indexes.s(processor_type_id, self.id,
        #                                  sender_type_id, instance_type_id, instance.id)
        #         | update_instance_indexes.s(processor_type_id, self.id,
        #                                     sender_type_id, instance_type_id, instance.id))
        #     chain()
        pass
