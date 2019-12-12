__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from rest_framework import serializers

from ..models import Event, StoredMessage, StoredMessageAttachment


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['uuid', 'data',]


class StoredMessageAttachmentLinkSerializer(serializers.ModelSerializer):
    link = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = StoredMessageAttachment
        fields = ['data', '_file', 'link']


class StoredMessageSerializer(serializers.ModelSerializer):
    attachments = StoredMessageAttachmentLinkSerializer(many=True)
    event_set = EventSerializer(many=True)

    class Meta:
        model = StoredMessage
        fields = ['uuid', 'data', 'datetimestamp', 'attachments', 'event_set']
