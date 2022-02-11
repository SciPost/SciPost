__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, response, serializers
from rest_framework.decorators import action

from .models import ConflictOfInterest
from .serializers import ConflictOfInterestSerializer


class IsEditorialAdministrator(permissions.BasePermission):
    """Check if User is Editorial Administrator to allow permission to API."""

    def has_object_permission(self, request, view, obj):
        """Check user's permissions."""
        return request.user.has_perm("scipost.can_oversee_refereeing")


class ConflictOfInterestViewSet(viewsets.ModelViewSet):
    """API view for ConflictOfInterest."""

    queryset = ConflictOfInterest.objects.all()
    serializer_class = ConflictOfInterestSerializer
    permission_classes = [permissions.IsAuthenticated, IsEditorialAdministrator]

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[IsEditorialAdministrator],
        url_path="verify-conflict",
        url_name="verify_conflict",
    )
    def verify_conflict(self, request, pk=None):
        """Verify a ConflictOfInterest or delete."""
        coi = get_object_or_404(ConflictOfInterest.objects.unverified(), pk=pk)
        if request.POST["status"] == "verified":
            coi.status = "verified"
        elif request.POST["status"] == "delete":
            coi.status = "deprecated"
        else:
            raise serializers.ValidationError("Invalid status value.")
        coi.save()
        serializer = self.serializer_class(coi)
        return response.Response(serializer.data)
