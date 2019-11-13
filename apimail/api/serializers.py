__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import Event, StoredMessage


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['uuid', 'data',]


class StoredMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoredMessage
        fields = ['uuid', 'data',]
