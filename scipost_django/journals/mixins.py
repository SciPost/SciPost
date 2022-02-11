__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .models import Publication

from scipost.mixins import PermissionsMixin


class PublicationMixin:
    model = Publication
    slug_field = slug_url_kwarg = "doi_label"


class ProdSupervisorPublicationPermissionMixin(PermissionsMixin):
    """
    This will give permission to Production Supervisors if Publication is in_draft.
    If Publication is not in draft, it will only give permission to administrators.
    """

    permission_required = "scipost.can_draft_publication"

    def has_permission(self):
        has_perm = super().has_permission()
        if has_perm and self.get_object().is_draft:
            return True
        return self.request.user.has_perm("scipost.can_publish_accepted_submission")
