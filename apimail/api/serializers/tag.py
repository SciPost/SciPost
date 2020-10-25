__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import UserTag


class UserTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTag
        fields = ['pk', 'user', 'label', 'unicode_symbol', 'variant']

    def get_queryset(self):
        user = self.context['request'].user
        return UserTag.objects.filter(user=user)
