__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from .models import ConflictOfInterest


class ConflictOfInterestSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConflictOfInterest
        fields = ('id', 'origin', 'to_contributor', 'type', 'status')
        read_only_fields = ('id', 'origin', 'to_contributor')
