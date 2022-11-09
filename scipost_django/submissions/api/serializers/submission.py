__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from submissions.models import Submission, Report
from submissions.api.serializers import (
    ReportPublicSerializer,
    SubmissionEventPublicSerializer,
)

from comments.models import Comment
from comments.api.serializers import CommentPublicSerializer
from preprints.api.serializers import PreprintPublicSerializer


class SubmissionPublicSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="preprint.identifier_w_vn_nr")
    url = serializers.URLField(source="get_absolute_url")
    publication = serializers.SerializerMethodField()
    acad_field = serializers.StringRelatedField()
    specialties = serializers.StringRelatedField(many=True)
    topics = serializers.StringRelatedField(many=True)
    approaches = serializers.StringRelatedField()
    submission_date = serializers.CharField(source="submission_date_ymd")
    is_resubmission_of = serializers.SerializerMethodField()
    submitted_to = serializers.StringRelatedField()
    thread_sequence_order = serializers.IntegerField()
    preprint = PreprintPublicSerializer()
    reports = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    # events = SubmissionEventPublicSerializer(many=True, read_only=True) # not useful

    class Meta:
        model = Submission
        fields = [
            "title",
            "author_list",
            "abstract",
            "identifier",
            "url",
            "publication",
            "acad_field",
            "specialties",
            "topics",
            "approaches",
            "status",
            "is_current",
            "submission_date",
            "original_submission_date",
            "submitted_to",
            "proceedings",
            "is_resubmission_of",
            "thread_hash",
            "thread_sequence_order",
            "code_repository_url",
            "data_repository_url",
            "preprint",
            "reports",
            "comments",
            "events",
        ]

    def get_publication(self, obj):
        if hasattr(obj, "publication") and obj.publication.is_published:
            return obj.publication.get_absolute_url()
        return None

    def get_is_resubmission_of(self, obj):
        if obj.is_resubmission_of:
            return obj.is_resubmission_of.get_absolute_url()
        return None

    def get_reports(self, obj):
        reports = obj.reports.accepted()
        return ReportPublicSerializer(reports, many=True, read_only=True).data

    def get_comments(self, obj):
        comments = obj.comments.vetted()
        return CommentPublicSerializer(comments, many=True, read_only=True).data


class SubmissionPublicSearchSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="preprint.identifier_w_vn_nr")
    submission_date = serializers.CharField(source="submission_date_ymd")
    original_submission_date = serializers.CharField(source="original_submission_date_ymd")
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
