__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from rest_framework import serializers

from ..models import (
    EmailAccount, EmailAccountAccess,
    Event,
    StoredMessage, StoredMessageAttachment,
    UserTag)


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = ['name', 'email', 'description']


class EmailAccountAccessSerializer(serializers.ModelSerializer):
    """For request.user, return list of email account accesses."""
    account = EmailAccountSerializer()
    rights = serializers.CharField(source='get_rights_display')

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


class UserTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTag
        fields = ['pk', 'label', 'unicode_symbol', 'variant']

    def get_queryset(self):
        user = self.request.user
        return UserTag.objects.filter(user=user)


class StoredMessageSerializer(serializers.ModelSerializer):
    attachments = StoredMessageAttachmentLinkSerializer(many=True)
    event_set = EventSerializer(many=True)
    read = serializers.SerializerMethodField()
    tags = UserTagSerializer(many=True)

    def get_read(self, obj):
        return self.context['request'].user in obj.read_by.all()

    class Meta:
        model = StoredMessage
        fields = ['uuid', 'data', 'datetimestamp', 'attachments', 'event_set', 'read', 'tags']
