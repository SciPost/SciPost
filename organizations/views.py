__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from .constants import ORGTYPE_PRIVATE_BENEFACTOR
from .forms import NewContactForm, ContactActivationForm
from .models import Organization, Contact

from funders.models import Funder
from mails.utils import DirectMailUtil
from organizations.decorators import has_contact
from partners.models import ProspectivePartner, Partner

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
            context['nr_prospartners_wo_organization'] = ProspectivePartner.objects.filter(
                organization=None).count()
            context['nr_partners_wo_organization'] = Partner.objects.filter(organization=None).count()
        context['pubyears'] = range(int(timezone.now().strftime('%Y')), 2015, -1)
        return context

    def get_queryset(self):
        qs = super().get_queryset().exclude(orgtype=ORGTYPE_PRIVATE_BENEFACTOR)
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

    def get_queryset(self):
        """
        Restrict view to permitted people if Organization details not publicly viewable.
        """
        queryset = super().get_queryset()
        if not self.request.user.has_perm('scipost.can_manage_organizations'):
            queryset = queryset.exclude(orgtype=ORGTYPE_PRIVATE_BENEFACTOR)
        return queryset


@permission_required('scipost.can_manage_SPB', return_403=True)
def organization_add_contact(request, organization_id):
    organization = get_object_or_404(Organization, id=organization_id)
    form = NewContactForm(request.POST or None, organization=organization)
    if form.is_valid():
        contact = form.save(current_user=request.user)
        mail_sender = DirectMailUtil(
            mail_code='org_contacts/email_contact_for_activation',
            contact=contact)
        mail_sender.send()
        messages.success(request, '<h3>Created contact: %s</h3>Email has been sent.'
                         % str(contact))
        return redirect(reverse('organizations:organization_details',
                                kwargs={'pk': organization.id}))
    context = {
        'organization': organization,
        'form': form
    }
    return render(request, 'organizations/organization_add_contact.html', context)


def activate_account(request, activation_key):
    contact = get_object_or_404(Contact, user__is_active=False,
                                activation_key=activation_key,
                                user__email__icontains=request.GET.get('email', None))

    # TODO: Key Expires fallback
    form = ContactActivationForm(request.POST or None, instance=contact.user)
    if form.is_valid():
        form.activate_user()
        messages.success(request, '<h3>Thank you for activating your account</h3>')
        return redirect(reverse('organizations:dashboard'))
    context = {
        'contact': contact,
        'form': form
    }
    return render(request, 'organizations/activate_account.html', context)


@login_required
def dashboard(request):
    """
    Administration page for Organization Contacts.

    This page is meant as a personal page for Contacts, where they will for example be able
    to read their personal data and agreements.
    """
    if not (request.user.has_perm('scipost.can_manage_organizations') or
            has_contact(request.user)):
        raise PermissionDenied

    context = {
        'roles': request.user.org_contact.roles.all()
    }

    return render(request, 'organizations/dashboard.html', context)
