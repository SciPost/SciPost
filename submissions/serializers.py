from rest_framework import serializers

from .models import Submission


class SubmissionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = (
            'title',
            'author_list',
            'arxiv_identifier_w_vn_nr',
            'discipline',
            'domain',
            'editor_in_charge',
            'is_current',
            'get_absolute_url',
            'submission_date',
            'acceptance_date'
        )
