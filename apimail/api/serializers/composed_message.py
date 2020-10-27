__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers
from rest_framework.exceptions import NotFound

from ...models import (
    ComposedMessage, ComposedMessageAPIResponse,
    AttachmentFile,
)
from ..serializers import AttachmentFileSerializer


class ComposedMessageAPIResponseSerializer(serializers.ModelSerializer):
    message_uuid = serializers.SerializerMethodField()

    class Meta:
        model = ComposedMessageAPIResponse
        fields = ['message_uuid', 'datetime', 'status_code', 'json']

    def get_message_uuid(self, obj):
        return obj.message.uuid


class ComposedMessageSerializer(serializers.ModelSerializer):
    from_email = serializers.SerializerMethodField()
    attachment_files = AttachmentFileSerializer(many=True, read_only=True)
    api_responses = ComposedMessageAPIResponseSerializer(many=True, read_only=True)

    class Meta:
        model = ComposedMessage
        fields = [
            'uuid', 'author', 'created_on', 'status',
            'from_account', 'from_email',
            'to_recipient', 'cc_recipients', 'bcc_recipients',
            'subject', 'body_text', 'body_html',
            'headers_added',
            'attachment_files', 'api_responses'
        ]

    def get_from_email(self, obj):
        return obj.from_account.email

    def validate(self, data):
        if data['status'] != ComposedMessage.STATUS_DRAFT:
            if not data['to_recipient']:
                raise serializers.ValidationError(
                    "to_recipient cannot be empty if message is not a draft")
            if not data['subject']:
                raise serializers.ValidationError(
                    "Subject cannot be empty if message is not a draft")
        return data

    def create(self, validated_data):
        attachment_uuids = validated_data.pop('attachment_uuids')
        cm = super().create(validated_data)
        # Now deal with attachments:
        # Check that files all exist; if not, save message as draft
        for att_uuid in attachment_uuids:
            try:
                att = AttachmentFile.objects.get(uuid=att_uuid)
                cm.attachment_files.add(att)
            except AttachmentFile.DoesNotExist:
                cm.status = ComposedMessage.STATUS_DRAFT
                cm.save()
                raise NotFound(detail=(
                    'The attachment file with uuid %s was not found. '
                    'Your message was saved as a draft (not sent).' % att_uuid))
        return cm

    def update(self, instance, validated_data):
        attachment_uuids = validated_data.pop('attachment_uuids')
        cm = super().update(instance, validated_data)
        # Now deal with attachments:
        # First remove any attachment which is not in the new list:
        pre_update_att_uuids = [att.uuid for att in cm.attachment_files.all()]
        for att in cm.attachment_files.all():
            if att.uuid not in attachment_uuids:
                cm.attachment_files.remove(att)
                # orphaned attachment files will be deleted automatically by the
                # cronjob running the delete_orphaned_attachment_files management command
        # Now add all new attachments:
        for att_uuid in attachment_uuids:
            if att_uuid not in pre_update_att_uuids:
                try:
                    att = AttachmentFile.objects.get(uuid=att_uuid)
                    cm.attachment_files.add(att)
                except AttachmentFile.DoesNotExist:
                    cm.status = ComposedMessage.STATUS_DRAFT
                    cm.save()
                    raise NotFound(detail=(
                        'The attachment file with uuid %s was not found. '
                        'Your message was saved as a draft (not sent).' % att_uuid))
        return cm
