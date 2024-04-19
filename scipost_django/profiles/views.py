__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from dal import autocomplete
from guardian.decorators import permission_required
from profiles import constants

from scipost.mixins import PermissionsMixin, PaginationMixin
from scipost.models import Contributor
from scipost.forms import SearchTextForm

from common.utils import Q_with_alternative_spellings
from invitations.models import RegistrationInvitation
from ontology.models import Specialty
from scipost.permissions import HTMXResponse, permission_required_htmx
from submissions.models import RefereeInvitation

from .models import Profile, ProfileEmail, Affiliation, ProfileNonDuplicates
from .forms import (
    ProfileForm,
    ProfileDynSelForm,
    ProfileMergeForm,
    AddProfileEmailForm,
    AffiliationForm,
)


################
# Autocomplete #
################


class ProfileAutocompleteView(autocomplete.Select2QuerySetView):
    """
    View to feed the Select2 widget.
    """

    def get_queryset(self):
        if not self.request.user.has_perm("scipost.can_view_profiles"):
            return None
        qs = Profile.objects.all()
        if self.q:
            qs = Profile.objects.search(self.q)

        return qs


class ProfileCreateView(PermissionsMixin, CreateView):
    """
    Formview to create a new Profile.
    """

    permission_required = "scipost.can_create_profiles"
    form_class = ProfileForm
    template_name = "profiles/profile_form.html"
    success_url = reverse_lazy("profiles:profiles")

    def get_context_data(self, *args, **kwargs):
        """
        When creating a Profile, if initial data obtained from another model
        (Contributor, RefereeInvitation or RegistrationInvitation)
        is provided, this fills the context with possible already-existing Profiles.
        """
        context = super().get_context_data(*args, **kwargs)
        from_type = self.kwargs.get("from_type", None)
        pk = self.kwargs.get("pk", None)
        context["from_type"] = from_type
        context["pk"] = pk
        if pk and from_type:
            matching_profiles = Profile.objects.all()
            if from_type == "contributor":
                contributor = get_object_or_404(Contributor, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=contributor.user.last_name)
                    | Q(emails__email__in=contributor.user.email)
                )
            elif from_type == "refereeinvitation":
                refinv = get_object_or_404(RefereeInvitation, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=refinv.last_name)
                    | Q(emails__email__in=refinv.email_address)
                )
            elif from_type == "registrationinvitation":
                reginv = get_object_or_404(RegistrationInvitation, pk=pk)
                matching_profiles = matching_profiles.filter(
                    Q(last_name=reginv.last_name) | Q(emails__email__in=reginv.email)
                )
            context["matching_profiles"] = matching_profiles.distinct().order_by(
                "last_name", "first_name"
            )
        return context

    def get_initial(self):
        """
        Provide initial data based on kwargs.
        The data can come from a Contributor, Invitation, ...
        """
        initial = super().get_initial()
        from_type = self.kwargs.get("from_type", None)
        pk = self.kwargs.get("pk", None)

        if pk and from_type:
            pk = int(pk)
            if from_type == "contributor":
                contributor = get_object_or_404(Contributor, pk=pk)
                initial.update(
                    {
                        "first_name": contributor.user.first_name,
                        "last_name": contributor.user.last_name,
                        "email": contributor.user.email,
                    }
                )
            elif from_type == "refereeinvitation":
                refinv = get_object_or_404(RefereeInvitation, pk=pk)
                initial.update(
                    {
                        "title": refinv.title,
                        "first_name": refinv.first_name,
                        "last_name": refinv.last_name,
                        "email": refinv.email_address,
                        "acad_field": refinv.submission.acad_field.id,
                        "specialties": [
                            s.id for s in refinv.submission.specialties.all()
                        ],
                    }
                )
            elif from_type == "registrationinvitation":
                reginv = get_object_or_404(RegistrationInvitation, pk=pk)
                initial.update(
                    {
                        "title": reginv.title,
                        "first_name": reginv.first_name,
                        "last_name": reginv.last_name,
                        "email": reginv.email,
                    }
                )
            initial.update(
                {
                    "instance_from_type": from_type,
                    "instance_pk": pk,
                }
            )
        return initial


@permission_required("scipost.can_create_profiles")
def profile_match(request, profile_id, from_type, pk):
    """
    Links an existing Profile to one of existing
    Contributor, RefereeInvitation or RegistrationInvitation.

    Profile relates to Contributor as OneToOne.
    Matching is thus only allowed if there are no duplicate objects for these elements.

    For matching the Profile to a Contributor, the following preconditions are defined:
    - the Profile has no association to another Contributor
    - the Contributor has no association to another Profile
    If these are not met, no action is taken.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    nr_rows = 0
    if from_type == "contributor":
        if hasattr(profile, "contributor") and profile.contributor.id != pk:
            messages.error(
                request,
                "Error: cannot math this Profile to this Contributor, "
                "since this Profile already has a different Contributor.\n"
                "Please merge the duplicate Contributors first.",
            )
            return redirect(reverse("profiles:profiles"))
        contributor = get_object_or_404(Contributor, pk=pk)
        if contributor.profile and contributor.profile.id != profile.id:
            messages.error(
                request,
                "Error: cannot match this Profile to this Contributor, "
                "since this Contributor already has a different Profile.\n"
                "Please merge the duplicate Profiles first.",
            )
            return redirect(reverse("profiles:profiles"))
        # Preconditions are met, match:
        nr_rows = Contributor.objects.filter(pk=pk).update(profile=profile)
        # Give priority to the email coming from Contributor
        profile.emails.update(primary=False)
        email, __ = ProfileEmail.objects.get_or_create(
            profile=profile, email=contributor.user.email
        )
        profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
    elif from_type == "refereeinvitation":
        nr_rows = RefereeInvitation.objects.filter(pk=pk).update(profile=profile)
    elif from_type == "registrationinvitation":
        nr_rows = RegistrationInvitation.objects.filter(pk=pk).update(profile=profile)
    if nr_rows == 1:
        messages.success(request, "Profile matched with %s" % from_type)
    else:
        messages.error(
            request,
            "Error: Profile matching with %s: updated %s rows instead of 1!"
            "Please contact techsupport" % (from_type, nr_rows),
        )
    return redirect(reverse("profiles:profiles"))


class ProfileUpdateView(PermissionsMixin, UpdateView):
    """
    Formview to update a Profile.
    """

    permission_required = "scipost.can_create_profiles"
    model = Profile
    form_class = ProfileForm
    template_name = "profiles/profile_form.html"
    success_url = reverse_lazy("profiles:profiles")


class ProfileDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a Profile.
    """

    permission_required = "scipost.can_create_profiles"
    model = Profile
    success_url = reverse_lazy("profiles:profiles")


class ProfileDetailView(PermissionsMixin, DetailView):
    permission_required = "scipost.can_view_profiles"
    model = Profile


class ProfileListView(PermissionsMixin, PaginationMixin, ListView):
    """
    List Profile object instances.
    """

    permission_required = "scipost.can_view_profiles"
    model = Profile
    paginate_by = 25

    def get_queryset(self):
        """
        Return a queryset of Profiles using optional GET data.
        """
        queryset = Profile.objects.all()
        if self.request.GET.get("field"):
            queryset = queryset.filter(acad_field__slug=self.request.GET["field"])
            if self.request.GET.get("specialty"):
                queryset = queryset.filter(
                    specialties__slug__in=[self.request.GET["specialty"]]
                )
        if self.request.GET.get("contributor") == "False":
            queryset = queryset.filter(contributor__isnull=True)
        elif self.request.GET.get("contributor") == "True":
            queryset = queryset.filter(contributor__isnull=False)
        if search_text := self.request.GET.get("text"):
            query = Q(last_name__unaccent__icontains=search_text)
            queryset = queryset.filter(query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contributors_w_duplicate_email = Contributor.objects.with_duplicate_email()
        contributors_w_duplicate_names = Contributor.objects.with_duplicate_names()
        contributors_wo_profile = Contributor.objects.nonduplicates().filter(
            profile__isnull=True
        )
        nr_potential_duplicate_profiles = Profile.objects.potential_duplicates().count()
        refinv_wo_profile = RefereeInvitation.objects.filter(profile__isnull=True)
        reginv_wo_profile = RegistrationInvitation.objects.filter(profile__isnull=True)

        context.update(
            {
                "searchform": SearchTextForm(
                    initial={"text": self.request.GET.get("text")}
                ),
                "nr_contributors_w_duplicate_emails": contributors_w_duplicate_email.count(),
                "nr_contributors_w_duplicate_names": contributors_w_duplicate_names.count(),
                "nr_contributors_wo_profile": contributors_wo_profile.count(),
                "nr_potential_duplicate_profiles": nr_potential_duplicate_profiles,
                "next_contributor_wo_profile": contributors_wo_profile.first(),
                "nr_refinv_wo_profile": refinv_wo_profile.count(),
                "next_refinv_wo_profile": refinv_wo_profile.first(),
                "nr_reginv_wo_profile": reginv_wo_profile.count(),
                "next_reginv_wo_profile": reginv_wo_profile.first(),
            }
        )
        return context


@login_required
@permission_required("scipost.can_merge_profiles")
def profile_duplicates(request):
    """
    List Profiles with potential duplicates; allow to merge if necessary.
    """
    # profile_duplicates = Profile.objects.potential_duplicates()
    # context = {
    #     "profile_duplicates": profile_duplicates,
    # }
    return render(request, "profiles/profile_duplicates.html")


@transaction.atomic
@permission_required_htmx(
    "scipost.can_merge_profiles",
    "You do not have permission to create profiles.",
)
def _hx_profile_mark_non_duplicate(request, profile1: int, profile2: int):
    # Find already existing ProfileNonDuplicates object, or create one if it doesn't exist
    prof_non_dupes = ProfileNonDuplicates.objects.filter(
        profiles__in=[profile1, profile2]
    ).first() or ProfileNonDuplicates.objects.create(reason=constants.DIFFERENT_PEOPLE)

    prof_non_dupes.profiles.add(profile1, profile2)
    return HTMXResponse(
        f"Profiles marked as different people.",
    )


@transaction.atomic
@permission_required_htmx(
    "scipost.can_merge_profiles",
    "You do not have permission to create profiles.",
)
def _hx_profile_merge(request, to_merge: int, to_merge_into: int):
    # Update the post data with the profiles to merge
    duplicate_profiles = Profile.objects.potential_duplicates()

    if request.method == "POST":
        post_data = {
            **(request.POST or {}),
            "to_merge": to_merge,
            "to_merge_into": to_merge_into,
        }
        merge_form = ProfileMergeForm(post_data)
        if merge_form.is_valid():
            profile = merge_form.save()
            messages.success(request, "Profiles merged successfully.")

    else:
        merge_form = ProfileMergeForm(
            queryset=duplicate_profiles,
            initial={
                "to_merge": duplicate_profiles[1].id,
                "to_merge_into": duplicate_profiles[0].id,
            },
        )

    context = {
        "duplicate_profiles": duplicate_profiles,
        "form": merge_form,
    }

    return render(request, "profiles/_hx_profile_merge.html", context)


@permission_required("scipost.can_merge_profiles")
def _hx_profile_comparison(request):
    if request.method == "GET":
        try:
            context = {
                "profile_to_merge": get_object_or_404(
                    Profile, pk=int(request.GET["to_merge"])
                ),
                "profile_to_merge_into": get_object_or_404(
                    Profile, pk=int(request.GET["to_merge_into"])
                ),
            }
        except ValueError:
            raise Http404

    return render(request, "profiles/_hx_profile_comparison.html", context)


@permission_required("scipost.can_create_profiles")
def _hx_profile_dynsel_list(request):
    form = ProfileDynSelForm(request.POST or None)
    if form.is_valid():
        profiles = form.search_results()
    else:
        profiles = Profile.objects.none()
    context = {
        "profiles": profiles,
        "action_url_name": form.cleaned_data["action_url_name"],
        "action_url_base_kwargs": (
            form.cleaned_data["action_url_base_kwargs"]
            if "action_url_base_kwargs" in form.cleaned_data
            else {}
        ),
        "action_target_element_id": form.cleaned_data["action_target_element_id"],
        "action_target_swap": form.cleaned_data["action_target_swap"],
    }
    return render(request, "profiles/_hx_profile_dynsel_list.html", context)


@permission_required("scipost.can_create_profiles")
def _hx_profile_specialties(request, profile_id):
    """
    Returns a snippet with current and possible specialties, with one-click actions.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    if request.method == "POST":
        specialty = get_object_or_404(Specialty, slug=request.POST.get("spec_slug"))
        if request.POST.get("action") == "add":
            profile.specialties.add(specialty)
        elif request.POST.get("action") == "remove":
            profile.specialties.remove(specialty)
    current_spec_slugs = [s.slug for s in profile.specialties.all()]
    other_specialties = Specialty.objects.filter(acad_field=profile.acad_field).exclude(
        slug__in=profile.specialties.values_list("slug")
    )
    context = {
        "profile": profile,
        "other_specialties": other_specialties,
    }
    return render(request, "profiles/_hx_profile_specialties.html", context)


@permission_required_htmx("scipost.can_add_profile_emails")
def _hx_add_profile_email(request, profile_id):
    """
    Add an email address to a Profile.
    """
    profile = get_object_or_404(Profile, pk=profile_id)
    form = AddProfileEmailForm(
        request.POST or None,
        profile=profile,
        request=request,
        hx_attrs={
            "hx-post": reverse(
                "profiles:_hx_add_profile_email", kwargs={"profile_id": profile.id}
            ),
            "hx-target": "next tbody",
            "hx-swap": "beforeend",
        },
        cancel_parent_tag="form",
    )
    if form.is_valid():
        profile_email = form.save()
        response = TemplateResponse(
            request,
            "profiles/_hx_profile_emails_table_row.html",
            {"profile_mail": profile_email},
        )

        return response

    return TemplateResponse(
        request, "profiles/_hx_add_profile_email_form.html", {"form": form}
    )


def _hx_profile_email_mark_primary(request, email_id):
    """
    Make this email the primary one for this Profile.
    """
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)

    is_mail_owner = request.user.contributor.profile == profile_email.profile
    can_validate_emails = request.user.has_perm("scipost.can_validate_profile_emails")
    if not (is_mail_owner or can_validate_emails):
        return HTMXResponse(
            "danger",
            "You do not have the required permissions to validate this email.",
        )

    if request.method == "PATCH":
        ProfileEmail.objects.filter(profile=profile_email.profile).update(primary=False)
        profile_email.primary = True
        profile_email.save()
    return TemplateResponse(
        request,
        "profiles/_hx_profile_emails_table.html",
        {"profile": profile_email.profile},
    )


def _hx_profile_email_toggle_valid(request, email_id):
    """Toggle valid/deprecated status of ProfileEmail."""

    profile_email = get_object_or_404(ProfileEmail, pk=email_id)

    is_mail_owner = request.user.contributor.profile == profile_email.profile
    can_validate_emails = request.user.has_perm("scipost.can_validate_profile_emails")
    if not (is_mail_owner or can_validate_emails):
        return HTMXResponse(
            "danger",
            "You do not have the required permissions to validate this email.",
        )

    if request.method == "PATCH":
        profile_email.still_valid = not profile_email.still_valid
        profile_email.save()
    return TemplateResponse(
        request,
        "profiles/_hx_profile_emails_table_row.html",
        {"profile_mail": profile_email},
    )


@permission_required_htmx("scipost.can_verify_profile_emails")
def _hx_profile_email_toggle_verified(request, email_id):
    """Toggle verified/unverified status of ProfileEmail."""
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)
    if request.method == "PATCH":
        profile_email.verified = not profile_email.verified
        profile_email.save()
    return TemplateResponse(
        request,
        "profiles/_hx_profile_emails_table_row.html",
        {"profile_mail": profile_email},
    )


@permission_required_htmx("scipost.can_delete_profile_emails")
def _hx_profile_email_delete(request, email_id):
    """Delete ProfileEmail."""
    profile_email = get_object_or_404(ProfileEmail, pk=email_id)
    if request.method == "DELETE":
        profile_email.delete()
    return HttpResponse("")


class AffiliationCreateView(UserPassesTestMixin, CreateView):
    model = Affiliation
    form_class = AffiliationForm
    template_name = "profiles/affiliation_form.html"

    def test_func(self):
        """
        Allow creating an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return True
        return (
            self.request.user.is_authenticated
            and self.request.user.contributor.profile.id
            == int(self.kwargs.get("profile_id"))
        )

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial(*args, **kwargs)
        profile = get_object_or_404(Profile, pk=self.kwargs.get("profile_id"))
        initial.update({"profile": profile})
        return initial

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return reverse_lazy(
                "profiles:profile_detail", kwargs={"pk": self.object.profile.id}
            )
        return reverse_lazy("scipost:personal_page")


class AffiliationUpdateView(UserPassesTestMixin, UpdateView):
    model = Affiliation
    form_class = AffiliationForm
    template_name = "profiles/affiliation_form.html"

    def test_func(self):
        """
        Allow updating an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return True
        return (
            self.request.user.is_authenticated
            and self.request.user.contributor.profile.id
            == int(self.kwargs.get("profile_id"))
        )

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return reverse_lazy(
                "profiles:profile_detail", kwargs={"pk": self.object.profile.id}
            )
        return reverse_lazy("scipost:personal_page")


class AffiliationDeleteView(UserPassesTestMixin, DeleteView):
    model = Affiliation

    def test_func(self):
        """
        Allow deleting an Affiliation if user is Admin, EdAdmin or is
        the Contributor to which this Profile is related.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return True
        return (
            self.request.user.is_authenticated
            and self.request.user.contributor.profile.id
            == int(self.kwargs.get("profile_id"))
        )

    def get_success_url(self):
        """
        If request.user is Admin or EdAdmin, redirect to profile detail view.
        Otherwise if request.user is Profile owner, return to personal page.
        """
        if self.request.user.has_perm("scipost.can_create_profiles"):
            return reverse_lazy(
                "profiles:profile_detail", kwargs={"pk": self.object.profile.id}
            )
        return reverse_lazy("scipost:personal_page")
