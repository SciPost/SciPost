__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import StoredMessage
from ..serializers import EventSerializer, AttachmentFileSerializer, UserTagSerializer


class StoredMessageSerializer(serializers.ModelSerializer):
    attachment_files = AttachmentFileSerializer(many=True)
    event_set = EventSerializer(many=True)
    read = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_read(self, obj):
        return self.context["request"].user in obj.read_by.all()

    def get_tags(self, obj):
        return UserTagSerializer(
            obj.tags.filter(user=self.context["request"].user), many=True
        ).data

    class Meta:
        model = StoredMessage
        fields = [
            "uuid",
            "data",
            "datetimestamp",
            "attachment_files",
            "event_set",
            "read",
            "tags",
        ]
