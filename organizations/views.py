__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse_lazy
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from .models import Organization

from funders.models import Funder
from partners.models import Partner

from scipost.mixins import PermissionsMixin


class OrganizationCreateView(PermissionsMixin, CreateView):
    """
    Create a new Organization.
    """
    permission_required = 'scipost.can_manage_organizations'
    model = Organization
    fields = '__all__'
    template_name = 'organizations/organization_create.html'
    success_url = reverse_lazy('organizations:organizations')


class OrganizationUpdateView(PermissionsMixin, UpdateView):
    """
    Update an Organization.
    """
    permission_required = 'scipost.can_manage_organizations'
    model = Organization
    fields = '__all__'
    template_name = 'organizations/organization_update.html'
    success_url = reverse_lazy('organizations:organizations')


class OrganizationDeleteView(PermissionsMixin, DeleteView):
    """
    Delete an Organization.
    """
    permission_required = 'scipost.can_manage_organizations'
    model = Organization
    success_url = reverse_lazy('organizations:organizations')


class OrganizationListView(ListView):
    model = Organization

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.has_perm('scipost.can_manage_organizations'):
            context['nr_funders_wo_organization'] = Funder.objects.filter(organization=None).count()
            context['nr_partners_wo_organization'] = Partner.objects.filter(organization=None).count()
        context['pubyears'] = range(int(timezone.now().strftime('%Y')), 2015, -1)
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        order_by = self.request.GET.get('order_by')
        ordering = self.request.GET.get('ordering')
        if order_by == 'country':
            qs = qs.order_by('country')
        elif order_by == 'name':
            qs = qs.order_by('name')
        elif order_by == 'nap':
            qs = qs.order_by('cf_nr_associated_publications')
        if ordering == 'desc':
            qs = qs.reverse()
        return qs


class OrganizationDetailView(DetailView):
    model = Organization

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['pubyears'] = range(int(timezone.now().strftime('%Y')), 2015, -1)
        return context
