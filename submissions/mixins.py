from django.contrib.auth.mixins import PermissionRequiredMixin

from .models import Submission


class FriendlyPermissionMixin(PermissionRequiredMixin):
    """
    This mixin controls the permissions with a fallback for anonymous users
    to help them login first. If a logged in user is refused, he will get the
    http 403 screen anyway.

    :permission_required: The permission code the user should comply with.
    """
    permission_required = 'scipost.dummy_permission'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        return super().dispatch(request, *args, **kwargs)


class SubmissionAdminViewMixin(FriendlyPermissionMixin):
    """
    This mixin will provide all basic methods and checks required for Submission
    administrational actions regarding Submissions.

    :editorial_page: Submission is element of the set pool() if False,
                     else Submission is element of the subset: editorial_page()
    """
    editorial_page = False
    slug_field = 'arxiv_identifier_w_vn_nr'
    slug_url_kwarg = 'arxiv_identifier_w_vn_nr'
    queryset = Submission.objects.all()

    @property
    def pool(self):
        return not self.editorial_page

    def get_queryset(self):
        qs = super().get_queryset()
        if self.pool:
            return qs.get_pool(self.request.user)
        return qs.filter_editorial_page(self.request.user)
