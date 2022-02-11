__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters


from ...models import StoredMessage, UserTag
from ..serializers import StoredMessageSerializer

from ...permissions import CanReadStoredMessage


class StoredMessageFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects.
    """

    def filter_queryset(self, request, queryset, view):
        queryset = StoredMessage.objects.all()
        queryfilter = Q()

        thread_of_uuid = request.query_params.get("thread_of_uuid", None)
        if thread_of_uuid:
            queryset = queryset.in_thread_of_uuid(thread_of_uuid)

        flow = request.query_params.get("flow", None)
        if flow == "in":
            # Restrict to incoming emails
            queryset = queryset.exclude(
                data__sender=request.query_params.get("account")
            )
        elif flow == "out":
            # Restrict to outgoing emails
            queryset = queryset.filter(data__sender=request.query_params.get("account"))

        period = request.query_params.get("period", "any")
        if period != "any":
            days = 365
            if period == "month":
                days = 31
            elif period == "week":
                days = 1
            limit = timezone.now() - datetime.timedelta(days=days)
            queryset = queryset.filter(datetimestamp__gt=limit)

        readstatus = request.query_params.get("read", None)
        if readstatus is not None:
            if readstatus == "true":
                queryset = queryset.filter(read_by__in=[request.user])
            elif readstatus == "false":
                queryset = queryset.exclude(read_by__in=[request.user])

        tagpklist = request.query_params.getlist("tag")
        if tagpklist:
            queryset = queryset.filter(tags__pk__in=tagpklist)

        _from = request.query_params.get("from", None)
        if _from is not None:
            queryfilter = queryfilter | Q(data__from__icontains=_from)
        subject = request.query_params.get("subject", None)
        if subject is not None:
            queryfilter = queryfilter | Q(data__subject__icontains=subject)
        recipients = request.query_params.get("recipients", None)
        if recipients is not None:
            queryfilter = queryfilter | Q(data__recipients__icontains=recipients)

        # For full-text searches through body-plain / body-html, we use a
        # raw SQL query since Django ORM does not support hyphenated lookups,
        # and since Mailgun uses hyphenated keys in its JSON responses.
        body = request.query_params.get("body", None)
        if body is not None:
            query_raw = (
                "SELECT apimail_storedmessage.id FROM apimail_storedmessage "
                "WHERE UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "OR UPPER((apimail_storedmessage.data ->> %s)::text) LIKE UPPER(%s) "
                "ORDER BY apimail_storedmessage.datetimestamp DESC;"
            )
            sm_ids = [
                sm.id
                for sm in StoredMessage.objects.raw(
                    query_raw,
                    ["body-plain", "%%%s%%" % body, "body-html", "%%%s%%" % body],
                )
            ]
            queryfilter = queryfilter | Q(pk__in=sm_ids)

        attachment_filename = request.query_params.get("attachment", None)
        if attachment_filename is not None:
            queryfilter = queryfilter | Q(
                attachment_files__data__name__icontains=attachment_filename
            )

        return queryset.filter(queryfilter).filter_for_user(
            request.user, request.query_params.get("account")
        )


class StoredMessageListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = "uuid"
    filter_backends = [
        StoredMessageFilterBackend,
    ]


class StoredMessageRetrieveAPIView(RetrieveAPIView):
    permission_classes = (
        IsAuthenticated,
        CanReadStoredMessage,
    )
    serializer_class = StoredMessageSerializer
    lookup_field = "uuid"


class StoredMessageUpdateReadAPIView(UpdateAPIView):
    """
    Updates the read field (M2M to user) in StoredMessage.
    """

    permission_classes = (
        IsAuthenticated,
        CanReadStoredMessage,
    )
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = "uuid"

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.read_by.add(request.user)
        instance.save()
        return Response()


class StoredMessageUpdateTagAPIView(UpdateAPIView):
    """
    Adds or removes a user tag on a StoredMessage.
    """

    permission_classes = [IsAuthenticated, CanReadStoredMessage]
    queryset = StoredMessage.objects.all()
    serializer_class = StoredMessageSerializer
    lookup_field = "uuid"

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        tag = get_object_or_404(UserTag, pk=self.request.data.get("tagpk"))
        action = self.request.data.get("action")
        if action == "add":
            instance.tags.add(tag)
        elif action == "remove":
            instance.tags.remove(tag)
        instance.save()
        return Response()
