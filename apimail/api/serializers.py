__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import Event, StoredMessage, StoredMessageAttachment


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['uuid', 'data',]


class StoredMessageAttachmentSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoredMessageAttachment
        fields = ['data', '_file']


class StoredMessageSerializer(serializers.ModelSerializer):
    attachments = StoredMessageAttachmentSimpleSerializer(many=True)

    class Meta:
        model = StoredMessage
        fields = ['uuid', 'data', 'datetimestamp', 'attachments']

    def create(self, validated_data):
        attachments_data = validated_data.pop('attachments')
        storedmessage = StoredMessage.objects.create(**validated_data)
        for attachment_data in attachments_data:
            StoredMessageAttachment.objects.create(
                message=storedmessage,
                **attachment_data)
        return storedmessage
