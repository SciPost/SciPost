__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import Submission


class SubmissionSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source='preprint.identifier_w_vn_nr')
    submission_date = serializers.CharField(source='submission_date_ymd')
    url = serializers.URLField(source='get_absolute_url')

    class Meta:
        model = Submission
        fields = [
            'title',
            'author_list',
            'abstract',
            'identifier',
            'submission_date',
            'original_submission_date',
            'url'
        ]
