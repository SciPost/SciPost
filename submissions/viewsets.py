from rest_framework import viewsets

from .models import Submission
from .serializers import SubmissionAdminSerializer


class SubmissionAdminViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubmissionAdminSerializer
    lookup_field = 'arxiv_identifier_w_vn_nr'
    lookup_value_regex = '[0-9]{4,}.[0-9]{5,}v[0-9]{1,2}'

    def get_queryset(self):
        return Submission.objects.get_pool(self.request.user)
