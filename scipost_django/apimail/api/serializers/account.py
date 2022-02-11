__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import EmailAccount, EmailAccountAccess


class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = ["pk", "name", "email", "description"]


class EmailAccountAccessSerializer(serializers.ModelSerializer):
    """For request.user, return list of email account accesses."""

    account = EmailAccountSerializer()
    rights = serializers.CharField(source="get_rights_display")

    class Meta:
        model = EmailAccountAccess
        fields = ["account", "rights", "date_from", "date_until"]
