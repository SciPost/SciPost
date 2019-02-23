__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.utils import timezone
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from .constants import ORGTYPE_PRIVATE_BENEFACTOR, ORGANIZATION_EVENT_EMAIL_SENT
from .forms import OrganizationEventForm, ContactPersonForm,\
    NewContactForm, ContactActivationForm, ContactRoleForm
from .models import Organization, OrganizationEvent, ContactPerson, Contact, ContactRole

from funders.models import Funder
from mails.utils import DirectMailUtil
from mails.views import MailEditingSubView
from organizations.decorators import has_contact
from partners.models import ProspectivePartner, Partner

from scipost.mixins import PermissionsMixin, PaginationMixin


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
            context['nr_partners_wo_organization'] = Partner.objects.filter(
                organization=None).count()
        context['pubyears'] = range(int(timezone.now().strftime('%Y')), 2015, -1)
        context['countrycodes'] = [code['country'] for code in list(
            Organization.objects.all().distinct('country').values('country'))]
        return context

    def get_queryset(self):
        qs = super().get_queryset().exclude(orgtype=ORGTYPE_PRIVATE_BENEFACTOR)
        country = self.request.GET.get('country')
        order_by = self.request.GET.get('order_by')
        ordering = self.request.GET.get('ordering')
        if country:
            qs = qs.filter(country=country)
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


class OrganizationEventCreateView(PermissionsMixin, CreateView):
    permission_required = 'scipost.can_manage_organizations'
    model = OrganizationEvent
    form_class = OrganizationEventForm
    template_name = 'organizations/organizationevent_form.html'

    def get_initial(self):
        organization = get_object_or_404(Organization, pk=self.kwargs.get('pk'))
        return {'organization': organization,
                'noted_on': timezone.now,
                'noted_by': self.request.user}

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


class ContactPersonCreateView(PermissionsMixin, CreateView):
    permission_required = 'scipost.can_add_contactperson'
    model = ContactPerson
    form_class= ContactPersonForm
    template_name = 'organizations/contactperson_form.html'

    def get_initial(self):
        organization = get_object_or_404(Organization, pk=self.kwargs.get('organization_id'))
        return {'organization': organization}

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


class ContactPersonUpdateView(PermissionsMixin, UpdateView):
    permission_required = 'scipost.can_add_contactperson'
    model = ContactPerson
    form_class= ContactPersonForm
    template_name = 'organizations/contactperson_form.html'

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


class ContactPersonDeleteView(UserPassesTestMixin, DeleteView):
    model = ContactPerson

    def test_func(self):
        """
        Allow ContactPerson delete to OrgAdmins and all Contacts for this Organization.
        """
        if self.request.user.has_perm('scipost.can_manage_organizations'):
            return True
        contactperson = get_object_or_404(ContactPerson, pk=self.kwargs.get('pk'))
        return self.request.user.has_perm('can_view_org_contacts', contactperson.organization)

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


@permission_required('scipost.can_manage_organizations', return_403=True)
@transaction.atomic
def email_contactperson(request, contactperson_id, mail=None):
    contactperson = get_object_or_404(ContactPerson, pk=contactperson_id)

    suffix = ''
    if mail == 'followup':
        code = 'org_contacts/contactperson_followup_mail'
        suffix = ' (followup)'
    else:
        code = 'org_contacts/contactperson_initial_mail'
        suffix = ' (initial)'
    mail_request = MailEditingSubView(request, mail_code=code, contactperson=contactperson)
    if mail_request.is_valid():
        comments = 'Email{suffix} sent to ContactPerson {name}.'.format(
            suffix=suffix, name=contactperson)
        event = OrganizationEvent(
            organization=contactperson.organization,
            event=ORGANIZATION_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user)
        event.save()
        messages.success(request, 'Email successfully sent.')
        mail_request.send()
        return redirect(contactperson.organization.get_absolute_url())
    else:
        return mail_request.return_render()


@permission_required('scipost.can_manage_SPB', return_403=True)
def organization_add_contact(request, organization_id, contactperson_id=None):
    organization = get_object_or_404(Organization, id=organization_id)
    if contactperson_id:
        contactperson = get_object_or_404(ContactPerson, id=contactperson_id)
        initial = {
            'title': contactperson.title,
            'first_name': contactperson.first_name,
            'last_name': contactperson.last_name,
            'email': contactperson.email
            }
    else:
        contactperson = None
        initial = {}
    form = NewContactForm(request.POST or None, initial=initial,
                          organization=organization,
                          contactperson=contactperson
    )
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
        'contacts': Contact.objects.all()
    }
    if has_contact(request.user):
        context['own_roles'] = request.user.org_contact.roles.all()
    return render(request, 'organizations/dashboard.html', context)


class ContactRoleUpdateView(UserPassesTestMixin,  UpdateView):
    """
    Update a ContactRole.
    """
    model = ContactRole
    form_class = ContactRoleForm
    template_name = 'organizations/contactrole_form.html'

    def test_func(self):
        """
        Allow ContactRole update to OrgAdmins and all Contacts for this Organization.
        """
        if self.request.user.has_perm('scipost.can_manage_organizations'):
            return True
        contactrole = get_object_or_404(ContactRole, pk=self.kwargs.get('pk'))
        return self.request.user.has_perm('can_view_org_contacts', contactrole.organization)

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


class ContactRoleDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a ContactRole.
    """
    permission_required = 'scipost.can_manage_organizations'
    model = ContactRole

    def get_success_url(self):
        return reverse_lazy('organizations:organization_details',
                            kwargs={'pk': self.object.organization.id})


@permission_required('scipost.can_manage_organizations', return_403=True)
@transaction.atomic
def email_contactrole(request, contactrole_id, mail=None):
    contactrole = get_object_or_404(ContactRole, pk=contactrole_id)

    suffix = ''
    if mail == 'renewal':
        code = 'org_contacts/contactrole_subsidy_renewal_mail'
        suffix = ' (subsidy renewal query)'
    else:
        code = 'org_contacts/contactrole_generic_mail'
        suffix = ' (generic)'
    mail_request = MailEditingSubView(request, mail_code=code, contactrole=contactrole)
    if mail_request.is_valid():
        comments = 'Email{suffix} sent to Contact {name}.'.format(
            suffix=suffix, name=contactrole.contact)
        event = OrganizationEvent(
            organization=contactrole.organization,
            event=ORGANIZATION_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user)
        event.save()
        messages.success(request, 'Email successfully sent.')
        mail_request.send()
        return redirect(contactrole.organization.get_absolute_url())
    else:
        return mail_request.return_render()
