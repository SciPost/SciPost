__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import QueryDict
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from dal import autocomplete
from guardian.decorators import permission_required

from .constants import (
    ORGTYPE_PRIVATE_BENEFACTOR,
    ORGANIZATION_EVENT_COMMENT,
    ORGANIZATION_EVENT_EMAIL_SENT,
)
from .forms import (
    SelectOrganizationForm,
    OrganizationForm,
    OrganizationEventForm,
    ContactPersonForm,
    NewContactForm,
    ContactActivationForm,
    ContactRoleForm,
)
from .models import Organization, OrganizationEvent, ContactPerson, Contact, ContactRole

from affiliates.models import AffiliateJournal
from funders.models import Funder
from mails.utils import DirectMailUtil
from mails.views import MailEditorSubview
from organizations.decorators import has_contact
from organizations.models import Organization

from organizations.utils import RORAPIHandler

from scipost.mixins import PermissionsMixin, PaginationMixin
from scipost.permissions import permission_required_htmx

######################
# Autocomplete views #
######################


class OrganizationAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.

    Flags of the organizations are displayed in the selection list;
    the stylesheet flags/sprite-hq.css from app django-countries
    must be accessible on the page for the flag to be displayed properly;
    we include it centrally in static and put this in the page head:

    .. code-block:: html

        <link rel="stylesheet" href="{% static 'flags/sprite-hq.css' %}">


    The data-html attribute has to be set to True on all widgets, e.g.

    .. code-block:: python

        organization = forms.ModelChoiceField(
            queryset=Organization.objects.all(),
            widget=autocomplete.ModelSelect2(
                url='/organizations/organization-autocomplete',
                attrs={'data-html': True}
            )
        )
    """

    def get_queryset(self):
        qs = Organization.objects.all()
        if self.q:
            qs = qs.filter(
                Q(name__unaccent__icontains=self.q)
                | Q(name_original__unaccent__icontains=self.q)
                | Q(acronym__unaccent__icontains=self.q)
                | Q(ror_json__names__contains=[{"value": self.q}])  # Search ROR
            )
        return qs

    def get_result_label(self, item):
        return format_html(
            '<span><i class="{}" data-bs-toggle="tooltip" title="{}"></i>&emsp;{}</span>',
            item.country.flag_css,
            item.country.name,
            item.name,
        )


class OrganizationCreateView(PermissionsMixin, CreateView):
    """
    Create a new Organization.
    """

    permission_required = "scipost.can_manage_organizations"
    form_class = OrganizationForm
    template_name = "organizations/organization_create.html"

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail", kwargs={"pk": self.object.id}
        )

    def has_permission(self):
        """
        Allow those with explicit permission and any
        affiliate journal managers to create organizations.
        """
        is_any_affiliate_manager = any(
            self.request.user.has_perm("manage_journal_content", journal)
            for journal in AffiliateJournal.objects.all()
        )
        self.is_any_affiliate_manager = (
            is_any_affiliate_manager and not self.request.user.is_superuser
        )

        return super().has_permission() or is_any_affiliate_manager

    def get_form_kwargs(self):
        """
        Update the form kwargs to include ROR data if requested.
        """
        kwargs = {}
        ror_id = self.request.POST.get("ror_id", None)

        ror_data = {}
        if ror_id:
            ror_data = RORAPIHandler.organization_from_ror_id(ror_id)
            if ror_data == {}:
                messages.error(self.request, "No ROR data found for this ID.")

            ror_data["ror_id"] = ror_id
            kwargs = {"initial": ror_data}

        # Replace POST data with the ROR data
        should_replace_ror = self.request.POST.get("fetch_ror", False)
        if should_replace_ror:
            # JSON fields need to be serialized for the "data" key
            ror_data["ror_json"] = json.dumps(ror_data["ror_json"])
            kwargs["data"] = ror_data

        return super().get_form_kwargs() | kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Disable all fields except orgtype, status and ror_id for affiliate managers
        if getattr(self, "is_any_affiliate_manager", False):
            for field in form.fields:
                form.fields[field].disabled = True

            form.fields["orgtype"].disabled = False
            form.fields["status"].disabled = False
            form.fields["ror_id"].disabled = False

            form.fields["ror_json"].required = True
            form.fields["ror_id"].required = True

        return form

    def form_valid(self, form):
        # Do not save the form if the user has only fetched ROR data
        if self.request.POST.get("fetch_ror", ""):
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_valid(form)


class OrganizationUpdateView(PermissionsMixin, UpdateView):
    """
    Update an Organization.
    """

    permission_required = "scipost.can_manage_organizations"
    model = Organization
    form_class = OrganizationForm
    template_name = "organizations/organization_update.html"

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail", kwargs={"pk": self.object.id}
        )

    def get_form_kwargs(self):
        """
        Update the form kwargs to include ROR data if requested.
        """
        kwargs = {}
        ror_id = self.request.POST.get("ror_id", None)

        ror_data = {}
        if ror_id:
            ror_data = RORAPIHandler.organization_from_ror_id(ror_id)
            if ror_data == {}:
                messages.error(self.request, "No ROR data found for this ID.")

            ror_data["ror_id"] = ror_id
            kwargs = {"initial": ror_data}

        # Replace POST data with the ROR data
        should_replace_ror = self.request.POST.get("fetch_ror", False)
        if should_replace_ror:
            # JSON fields need to be serialized for the "data" key
            ror_data["ror_json"] = json.dumps(ror_data["ror_json"])
            kwargs["data"] = ror_data

        return super().get_form_kwargs() | kwargs

    def form_valid(self, form):
        # Do not save the form if the user has only fetched ROR data
        if self.request.POST.get("fetch_ror", ""):
            return self.render_to_response(self.get_context_data(form=form))

        return super().form_valid(form)


class OrganizationDeleteView(PermissionsMixin, DeleteView):
    """
    Delete an Organization.
    """

    permission_required = "scipost.can_manage_organizations"
    model = Organization
    success_url = reverse_lazy("organizations:organizations")


class OrganizationListView(PaginationMixin, ListView):
    model = Organization
    paginate_by = 50

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.has_perm("scipost.can_manage_organizations"):
            context["nr_funders_wo_organization"] = Funder.objects.filter(
                organization=None
            ).count()
        context["countrycodes"] = [
            code["country"]
            for code in list(
                Organization.objects.all().distinct("country").values("country")
            )
        ]
        context["select_organization_form"] = SelectOrganizationForm()
        return context

    def get_queryset(self):
        qs = super().get_queryset().exclude(orgtype=ORGTYPE_PRIVATE_BENEFACTOR)
        country = self.request.GET.get("country")
        order_by = self.request.GET.get("order_by")
        ordering = self.request.GET.get("ordering")
        if country:
            qs = qs.filter(country=country)
        if order_by == "country":
            qs = qs.order_by("country")
        elif order_by == "name":
            qs = qs.order_by("name")
        elif order_by == "nap":
            qs = qs.exclude(cf_nr_associated_publications__isnull=True).order_by(
                "cf_nr_associated_publications"
            )
        elif order_by == "impact":
            qs = qs.order_by("cf_balance_info__cumulative__impact_on_reserves")
        if ordering == "desc":
            qs = qs.reverse()
        return qs.prefetch_related("logos")


def get_organization_detail(request):
    org_id = request.GET.get("organization", None)
    if org_id:
        return redirect(
            reverse("organizations:organization_detail", kwargs={"pk": org_id})
        )
    return redirect(reverse("organizations:organizations"))


class OrganizationDetailView(DetailView):
    model = Organization

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["balance"] = self.object.cf_balance_info
        return context

    def get_queryset(self):
        """
        Restrict view to permitted people if Organization details not publicly viewable.
        """
        queryset = super().get_queryset()
        if not self.request.user.has_perm("scipost.can_manage_organizations"):
            queryset = queryset.exclude(orgtype=ORGTYPE_PRIVATE_BENEFACTOR)
        # return queryset
        return queryset.select_related("parent").prefetch_related(
            "children",
            "subsidy_set",
            "contactperson_set",
            "contactrole_set",
            "funder_set",
            "organizationevent_set",
            "pubfracs",
        )


class OrganizationEventCreateView(PermissionsMixin, CreateView):
    permission_required = "scipost.can_manage_organizations"
    model = OrganizationEvent
    form_class = OrganizationEventForm
    template_name = "organizations/organizationevent_form.html"

    def get_initial(self):
        organization = get_object_or_404(Organization, pk=self.kwargs.get("pk"))
        return {
            "organization": organization,
            "noted_on": timezone.now,
            "noted_by": self.request.user,
        }

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


class OrganizationEventListView(PermissionsMixin, PaginationMixin, ListView):
    permission_required = "scipost.can_manage_organizations"
    model = OrganizationEvent
    paginate_by = 10


class ContactPersonCreateView(PermissionsMixin, CreateView):
    permission_required = "scipost.can_add_contactperson"
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = "organizations/contactperson_form.html"

    def get_initial(self):
        try:
            organization = Organization.objects.get(
                pk=self.kwargs.get("organization_id")
            )
            return {"organization": organization}
        except Organization.DoesNotExist:
            pass

    def form_valid(self, form):
        event = OrganizationEvent(
            organization=form.cleaned_data["organization"],
            event=ORGANIZATION_EVENT_COMMENT,
            comments=(
                "Added ContactPerson: %s %s"
                % (form.cleaned_data["first_name"], form.cleaned_data["last_name"])
            ),
            noted_on=timezone.now(),
            noted_by=self.request.user,
        )
        event.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


class ContactPersonUpdateView(PermissionsMixin, UpdateView):
    permission_required = "scipost.can_add_contactperson"
    model = ContactPerson
    form_class = ContactPersonForm
    template_name = "organizations/contactperson_form.html"

    def form_valid(self, form):
        event = OrganizationEvent(
            organization=form.cleaned_data["organization"],
            event=ORGANIZATION_EVENT_COMMENT,
            comments=(
                "Updated ContactPerson: %s %s"
                % (form.cleaned_data["first_name"], form.cleaned_data["last_name"])
            ),
            noted_on=timezone.now(),
            noted_by=self.request.user,
        )
        event.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


class ContactPersonDeleteView(UserPassesTestMixin, DeleteView):
    model = ContactPerson

    def test_func(self):
        """
        Allow ContactPerson delete to OrgAdmins and all Contacts for this Organization.
        """
        if self.request.user.has_perm("scipost.can_manage_organizations"):
            return True
        contactperson = get_object_or_404(ContactPerson, pk=self.kwargs.get("pk"))
        return self.request.user.has_perm(
            "can_view_org_contacts", contactperson.organization
        )

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


class ContactPersonListView(PermissionsMixin, ListView):
    permission_required = "scipost.can_add_contactperson"
    model = ContactPerson


@permission_required("scipost.can_manage_organizations", return_403=True)
@transaction.atomic
def email_contactperson(request, contactperson_id, mail=None):
    contactperson = get_object_or_404(ContactPerson, pk=contactperson_id)

    suffix = ""
    if mail == "followup":
        mail_code = "org_contacts/contactperson_followup_mail"
        suffix = " (followup)"
    elif mail == "sos2024":
        mail_code = "org_contacts/contactperson_sos2024"
        suffix = " (sos2024)"
    else:
        mail_code = "org_contacts/contactperson_initial_mail"
        suffix = " (initial)"
    mail_request = MailEditorSubview(request, mail_code, contactperson=contactperson)
    if mail_request.is_valid():
        comments = "Email{suffix} sent to ContactPerson {name}.".format(
            suffix=suffix, name=contactperson
        )
        event = OrganizationEvent(
            organization=contactperson.organization,
            event=ORGANIZATION_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user,
        )
        event.save()
        messages.success(request, "Email successfully sent.")
        mail_request.send_mail()
        return redirect(contactperson.organization.get_absolute_url())
    else:
        return mail_request.interrupt()


@permission_required("scipost.can_manage_organizations", return_403=True)
def organization_add_contact(request, organization_id, contactperson_id=None):
    organization = get_object_or_404(Organization, id=organization_id)
    if contactperson_id:
        contactperson = get_object_or_404(ContactPerson, id=contactperson_id)
        initial = {
            "title": contactperson.title,
            "first_name": contactperson.first_name,
            "last_name": contactperson.last_name,
            "email": contactperson.email,
        }
    else:
        contactperson = None
        initial = {}
    form = NewContactForm(
        request.POST or None,
        initial=initial,
        organization=organization,
        contactperson=contactperson,
    )
    if form.is_valid():
        contact = form.save(current_user=request.user)
        mail_sender = DirectMailUtil(
            "org_contacts/email_contact_for_activation", contact=contact
        )
        mail_sender.send_mail()
        for role in contact.roles.all():
            event = OrganizationEvent(
                organization=role.organization,
                event=ORGANIZATION_EVENT_COMMENT,
                comments=("Contact for %s created; activation pending" % str(contact)),
                noted_on=timezone.now(),
                noted_by=request.user,
            )
            event.save()
        messages.success(
            request, "<h3>Created contact: %s</h3>Email has been sent." % str(contact)
        )
        return redirect(
            reverse("organizations:organization_detail", kwargs={"pk": organization.id})
        )
    context = {"organization": organization, "form": form}
    return render(request, "organizations/organization_add_contact.html", context)


def activate_account(request, activation_key):
    contact = get_object_or_404(
        Contact,
        user__is_active=False,
        activation_key=activation_key,
        user__email__icontains=request.GET.get("email", None),
    )

    # TODO: Key Expires fallback
    form = ContactActivationForm(request.POST or None, instance=contact.user)
    if form.is_valid():
        form.activate_user()
        for role in contact.roles.all():
            event = OrganizationEvent(
                organization=role.organization,
                event=ORGANIZATION_EVENT_COMMENT,
                comments=("Contact %s activated their account" % str(contact)),
                noted_on=timezone.now(),
                noted_by=contact.user,
            )
            event.save()
        messages.success(request, "<h3>Thank you for activating your account</h3>")
        return redirect(reverse("organizations:dashboard"))
    context = {"contact": contact, "form": form}
    return render(request, "organizations/activate_account.html", context)


@login_required
def dashboard(request):
    """
    Administration page for Organization Contacts.

    This page is meant as a personal page for Contacts, where they will for example be able
    to read their personal data and agreements.
    """
    if not (
        request.user.has_perm("scipost.can_manage_organizations")
        or has_contact(request.user)
    ):
        raise PermissionDenied
    context = {"contacts": Contact.objects.all()}
    if has_contact(request.user):
        context["own_roles"] = request.user.org_contact.roles.all()
    return render(request, "organizations/dashboard.html", context)


class ContactDetailView(PermissionsMixin, DetailView):
    """
    View details of a Contact. Accessible to Admin.
    """

    permission_required = "scipost.can_manage_organizations"
    model = Contact


class ContactRoleUpdateView(UserPassesTestMixin, UpdateView):
    """
    Update a ContactRole.
    """

    model = ContactRole
    form_class = ContactRoleForm
    template_name = "organizations/contactrole_form.html"

    def test_func(self):
        """
        Allow ContactRole update to OrgAdmins and all Contacts for this Organization.
        """
        if self.request.user.has_perm("scipost.can_manage_organizations"):
            return True
        contactrole = get_object_or_404(ContactRole, pk=self.kwargs.get("pk"))
        return self.request.user.has_perm(
            "can_view_org_contacts", contactrole.organization
        )

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


class ContactRoleDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a ContactRole.
    """

    permission_required = "scipost.can_manage_organizations"
    model = ContactRole

    def get_success_url(self):
        return reverse_lazy(
            "organizations:organization_detail",
            kwargs={"pk": self.object.organization.id},
        )


@permission_required("scipost.can_manage_organizations", return_403=True)
@transaction.atomic
def email_contactrole(request, contactrole_id, mail=None):
    contactrole = get_object_or_404(ContactRole, pk=contactrole_id)

    suffix = ""
    if mail == "renewal":
        mail_code = "org_contacts/contactrole_subsidy_renewal_mail"
        suffix = " (subsidy renewal query)"
    else:
        mail_code = "org_contacts/contactrole_generic_mail"
        suffix = " (generic)"
    mail_request = MailEditorSubview(request, mail_code, contactrole=contactrole)
    if mail_request.is_valid():
        comments = "Email{suffix} sent to Contact {name}.".format(
            suffix=suffix, name=contactrole.contact
        )
        event = OrganizationEvent(
            organization=contactrole.organization,
            event=ORGANIZATION_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user,
        )
        event.save()
        messages.success(request, "Email successfully sent.")
        mail_request.send_mail()
        return redirect(contactrole.organization.get_absolute_url())
    else:
        return mail_request.interrupt()


### ROR ###
@permission_required_htmx("scipost.can_manage_organizations")
def _hx_ror_search_form(request, pk):
    """
    Helper function to generate the form for ROR search.
    """
    from organizations.forms import RORSearchForm

    organization = get_object_or_404(Organization, id=pk)
    form = RORSearchForm(query=organization.name)

    return TemplateResponse(
        request,
        "organizations/_hx_ror_search_form.html",
        {"organization": organization, "form": form},
    )


@permission_required_htmx("scipost.can_manage_organizations")
# @for_htmx(use_block_from_params=True)
def _hx_ror_search_results(request, pk):
    """
    Perform ROR search and return results.
    """

    ror_api_handler = RORAPIHandler()
    results = ror_api_handler.query(request.POST["query"])

    return TemplateResponse(
        request,
        "organizations/_hx_ror_search_results.html",
        {"pk": pk, "results": results},
    )


@permission_required_htmx("scipost.can_manage_organizations")
# @for_htmx(use_block_from_params=True)
def _hx_add_ror(request, pk, ror_id):
    """
    Get ROR data and add it to the organization.
    """

    organization = get_object_or_404(Organization, id=pk)
    ror_api_handler = RORAPIHandler()

    if ror_id == "None":
        organization.ror_json = {}
    else:
        ror_data = ror_api_handler.fetch(ror_id)
        organization.ror_json = ror_data

    organization.save()

    return TemplateResponse(
        request,
        "organizations/_hx_organization_info.html",
        {"org": organization},
    )
