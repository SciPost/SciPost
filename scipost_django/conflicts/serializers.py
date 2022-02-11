__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from .models import ConflictOfInterest


class ConflictOfInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConflictOfInterest
        fields = ("id", "related_profile", "profile", "type", "status")
        read_only_fields = ("id", "related_profile", "profile")
