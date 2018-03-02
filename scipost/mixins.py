from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .paginator import SciPostPaginator


class PermissionsMixin(LoginRequiredMixin, PermissionRequiredMixin):
    pass


class PaginationMixin:
    """
    Mixin for generic class-based views (e.g. django.views.generic.ListView)
    """
    paginator_class = SciPostPaginator
