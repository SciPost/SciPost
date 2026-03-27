__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from submissions.models import Submission, Report
from submissions.api.serializers import (
    ReportPublicSerializer,
)
from comments.api.serializers import CommentPublicSerializer
from preprints.api.serializers import PreprintPublicSerializer


class SubmissionPublicSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="preprint.identifier_w_vn_nr")
    url = serializers.URLField(source="get_absolute_url")
    publications = serializers.SerializerMethodField()
    acad_field = serializers.StringRelatedField()
    specialties = serializers.StringRelatedField(many=True)
    topics = serializers.StringRelatedField(many=True)
    approaches = serializers.StringRelatedField()
    is_resubmission_of = serializers.SerializerMethodField()
    submitted_to = serializers.StringRelatedField()
    preprint = PreprintPublicSerializer()
    reports = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "title",
            "author_list",
            "abstract",
            "identifier",
            "url",
            "publications",
            "acad_field",
            "specialties",
            "topics",
            "approaches",
            "status",
            "submission_date",
            "original_submission_date",
            "submitted_to",
            "proceedings",
            "is_resubmission_of",
            "thread_hash",
            "preprint",
            "reports",
            "comments",
            "events",
        ]

    def get_publications(self, obj):
        return [{"url": pub.get_absolute_url()} for pub in obj.published_publications]

    def get_is_resubmission_of(self, obj):
        if obj.is_resubmission_of:
            return obj.is_resubmission_of.get_absolute_url()
        return None

    def get_reports(self, obj):
        return ReportPublicSerializer(
            obj.accepted_reports, many=True, read_only=True
        ).data

    def get_comments(self, obj):
        return CommentPublicSerializer(
            obj.vetted_comments, many=True, read_only=True
        ).data

    def get_events(self, obj):
        return [
            {"created": event.created, "text": event.text}
            for event in obj.public_events
        ]


class SubmissionPublicSearchSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="preprint.identifier_w_vn_nr")
    submission_date = serializers.CharField(source="submission_date_ymd")
    original_submission_date = serializers.CharField(
        source="original_submission_date_ymd"
    )
    url = serializers.URLField(source="get_absolute_url")

    class Meta:
        model = Submission
        fields = [
            "title",
            "author_list",
            "abstract",
            "identifier",
            "submission_date",
            "original_submission_date",
            "url",
        ]
