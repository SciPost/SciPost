__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .paginator import SciPostPaginator


class PermissionsMixin(LoginRequiredMixin, PermissionRequiredMixin):
    pass


class PaginationMixin:
    """
    Mixin for generic class-based views (e.g. django.views.generic.ListView)
    """
    paginator_class = SciPostPaginator


class RequestViewMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
