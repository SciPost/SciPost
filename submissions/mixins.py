from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.list import ListView

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


class SubmissionFormViewMixin:
    def get_form_kwargs(self):
        """
        Ideally all ModelForms on Submission-related objects have a required argument `submission`.
        """
        kwargs = super().get_form_kwargs()
        kwargs['submission'] = self._original_submission
        return kwargs


class SubmissionAdminViewMixin(FriendlyPermissionMixin, SubmissionFormViewMixin):
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
        """
        Return either of two sets of Submissions, with an author filter for the current user.

        This method is used in all Class-Based-Views. However, if one overwrites either one of the
         - get_object()
         - get_queryset()
        methods, please don't forget to call super().method_name() to not remove this filter!
        """
        qs = super().get_queryset()
        if self.pool:
            return qs.get_pool(self.request.user)
        return qs.filter_editorial_page(self.request.user)

    def get_object(self):
        """
        Save the original Submission instance for performance reasons to the view,
        which may be used in get_context_data().
        """
        obj = super().get_object()
        self.submission = obj
        return obj

    def get_context_data(self, *args, **kwargs):
        """
        If the main object in a DetailView is not a Submission instance, it will be lost.
        Here, explicitly save the Submission instance to the context data.
        """
        ctx = super().get_context_data(*args, **kwargs)

        if not ctx.get('submission') and not isinstance(self, ListView):
            # Call parent get_object() to explicitly save the submission which is related
            # to the view's main object.
            ctx['submission'] = self._original_submission
        return ctx

    @property
    def _original_submission(self):
        if hasattr(self, 'submission'):
            return self.submission
        obj = super().get_object()
        if isinstance(obj, Submission):
            return obj
        return None
