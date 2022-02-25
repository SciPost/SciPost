__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import SubmissionEvent


class SubmissionEventPublicSerializer(serializers.ModelSerializer):
    event = serializers.CharField(source="get_event_display")

    class Meta:
        model = SubmissionEvent
        fields = [
            "created",
            "event",
            "submission",
        ]
