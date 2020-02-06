__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from rest_framework import serializers

from ..models import (
    AttachmentFile,
    EmailAccount, EmailAccountAccess,
    ComposedMessage,
    Event,
    StoredMessage,
    UserTag)


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = ['pk', 'name', 'email', 'description']


class EmailAccountAccessSerializer(serializers.ModelSerializer):
    """For request.user, return list of email account accesses."""
    account = EmailAccountSerializer()
    rights = serializers.CharField(source='get_rights_display')

    class Meta:
        model = EmailAccountAccess
        fields = ['account', 'rights', 'date_from', 'date_until']


class AttachmentFileSerializer(serializers.ModelSerializer):
    link = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = AttachmentFile
        fields = ['uuid', 'data', 'file', 'link']


class ComposedMessageSerializer(serializers.ModelSerializer):
    attachment_files = AttachmentFileSerializer(many=True, read_only=True)

    class Meta:
        model = ComposedMessage
        fields = ['uuid', 'author', 'created_on', 'status',
                  'from_account', 'to_recipient', 'cc_recipients', 'bcc_recipients',
                  'subject', 'body_text', 'body_html',
                  'attachment_files'
        ]

    def create(self, validated_data):
        # TODO
        cm = super().create(validated_data)
        return cm

    def update(self, instance, validated_data):
        # TODO
        cm = super().update(instance, validated_data)
        return cm


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['uuid', 'data',]


class UserTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTag
        fields = ['pk', 'label', 'unicode_symbol', 'variant']

    def get_queryset(self):
        user = self.request.user
        return UserTag.objects.filter(user=user)


class StoredMessageSerializer(serializers.ModelSerializer):
    attachment_files = AttachmentFileSerializer(many=True)
    event_set = EventSerializer(many=True)
    read = serializers.SerializerMethodField()
    tags = UserTagSerializer(many=True)

    def get_read(self, obj):
        return self.context['request'].user in obj.read_by.all()

    class Meta:
        model = StoredMessage
        fields = ['uuid', 'data', 'datetimestamp', 'attachment_files', 'event_set', 'read', 'tags']
