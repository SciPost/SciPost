__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from rest_framework import serializers

from ..models import (
    EmailAccount, EmailAccountAccess,
    Event,
    StoredMessage, StoredMessageAttachment)


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = ['name', 'email', 'description']


class EmailAccountAccessSerializer(serializers.ModelSerializer):
    """For request.user, return list of email account accesses."""
    account = EmailAccountSerializer()

    class Meta:
        model = EmailAccountAccess
        fields = ['account', 'rights', 'date_from', 'date_until']


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
