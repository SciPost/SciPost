__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import reduce
import re
from django import forms
from django.db.models import Q

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete
from django.forms import ChoiceField
from django.urls import reverse

from common.forms import ModelChoiceFieldwithid
from invitations.models import RegistrationInvitation
from organizations.models import Organization
from scipost.models import Contributor
from submissions.models import RefereeInvitation

from .models import Profile, ProfileEmail, Affiliation


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False)
    # If the Profile is created from an existing object (so we can update the object):
    instance_from_type = forms.CharField(max_length=32, required=False)
    instance_pk = forms.IntegerField(required=False)

    class Meta:
        model = Profile
        fields = [
            "title",
            "first_name",
            "last_name",
            "orcid_id",
            "webpage",
            "acad_field",
            "specialties",
            "topics",
            "accepts_SciPost_emails",
            "accepts_refereeing_requests",
            "instance_from_type",
            "instance_pk",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].initial = self.instance.email
        self.fields["instance_from_type"].widget = forms.HiddenInput()
        self.fields["instance_pk"].widget = forms.HiddenInput()

    def clean_email(self):
        """Check that the email isn't yet associated to an existing Profile."""
        cleaned_email = self.cleaned_data["email"]
        if (
            cleaned_email
            and ProfileEmail.objects.filter(email=cleaned_email)
            .exclude(profile__id=self.instance.id)
            .exists()
        ):
            raise forms.ValidationError("A Profile with this email already exists.")
        return cleaned_email

    def clean_instance_from_type(self):
        """
        Check that only recognized types are used.
        """
        cleaned_instance_from_type = self.cleaned_data["instance_from_type"]
        if cleaned_instance_from_type not in [
            "",
            "contributor",
            "refereeinvitation",
            "registrationinvitation",
        ]:
            raise forms.ValidationError("The from_type hidden field is inconsistent.")
        return cleaned_instance_from_type

    def save(self):
        profile = super().save()
        if self.cleaned_data["email"]:
            profile.emails.update(primary=False)
            email, __ = ProfileEmail.objects.get_or_create(
                profile=profile, email=self.cleaned_data["email"]
            )
            profile.emails.filter(id=email.id).update(primary=True, still_valid=True)
        instance_pk = self.cleaned_data["instance_pk"]
        if instance_pk:
            if self.cleaned_data["instance_from_type"] == "contributor":
                Contributor.objects.filter(pk=instance_pk).update(profile=profile)
            elif self.cleaned_data["instance_from_type"] == "refereeinvitation":
                RefereeInvitation.objects.filter(pk=instance_pk).update(profile=profile)
            elif self.cleaned_data["instance_from_type"] == "registrationinvitation":
                RegistrationInvitation.objects.filter(pk=instance_pk).update(
                    profile=profile
                )
        return profile


class SimpleProfileForm(ProfileForm):
    """
    Simple version of ProfileForm, displaying only required fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["orcid_id"].widget = forms.HiddenInput()
        self.fields["webpage"].widget = forms.HiddenInput()
        self.fields["acad_field"].widget = forms.HiddenInput()
        self.fields["specialties"].widget = forms.HiddenInput()
        self.fields["topics"].widget = forms.HiddenInput()
        self.fields["accepts_SciPost_emails"].widget = forms.HiddenInput()
        self.fields["accepts_refereeing_requests"].widget = forms.HiddenInput()


class ProfileMergeForm(forms.Form):
    to_merge = ModelChoiceFieldwithid(
        queryset=Profile.objects.potential_duplicates(),
        empty_label=None,
        label="Merge this profile",
    )
    to_merge_into = ModelChoiceFieldwithid(
        queryset=Profile.objects.potential_duplicates(),
        empty_label=None,
        label="into this profile",
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop("queryset", None)
        super().__init__(*args, **kwargs)
        if queryset:
            self.fields["to_merge"].queryset = queryset
            self.fields["to_merge_into"].queryset = queryset

        self.helper = FormHelper()
        self.helper.attrs = {
            "hx-target": "#merge-form-info",
            "hx-get": reverse(
                "profiles:_hx_profile_comparison",
            ),
            "hx-trigger": "intersect once, change from:select",
        }
        self.layout = Layout(
            Div(
                Div(
                    Field("to_merge"),
                    css_id="to_merge",
                    css_class="col-12 col-md",
                ),
                Div(
                    Field("to_merge_into"),
                    css_id="to_merge_into",
                    css_class="col-12 col-md",
                ),
                css_class="row mb-0",
            ),
            Div(
                Div(
                    css_class="col-12",
                    css_id="merge-form-info",
                ),
                css_class="row mb-0",
            ),
        )
        self.helper.layout = self.layout

    def clean(self):
        """
        To merge Profiles, they must be distinct, and it must not be the
        case that they both are associated to a Contributor instance
        (which would mean two Contributor objects for the same person).
        """
        data = super().clean()
        if self.cleaned_data["to_merge"] == self.cleaned_data["to_merge_into"]:
            self.add_error(None, "A Profile cannot be merged into itself.")
        if (
            self.cleaned_data["to_merge"].has_active_contributor
            and self.cleaned_data["to_merge_into"].has_active_contributor
        ):
            self.add_error(
                None,
                "Each of these two Profiles has an active Contributor. "
                "Merge the Contributors first.\n"
                "If these are distinct people or if two separate "
                "accounts are needed, a ProfileNonDuplicate instance should be created.",
            )
        return data

    def save(self):
        """
        Perform the actual merge: save all data from to-be-deleted profile
        into the one to be kept.
        """
        profile = self.cleaned_data["to_merge_into"]
        profile_old = self.cleaned_data["to_merge"]

        # Merge information from old to new Profile.
        if profile.orcid_id is None:
            profile.orcid_id = profile_old.orcid_id
        if profile.webpage is None:
            profile.webpage = profile_old.webpage
        if profile.acad_field is None:
            profile.acad_field = profile_old.acad_field
        if profile_old.has_active_contributor and not profile.has_active_contributor:
            profile.contributor = profile_old.contributor
        profile.save()  # Save all the field updates.

        profile.specialties.add(*profile_old.specialties.all())
        profile.topics.add(*profile_old.topics.all())

        # Merge email
        profile_old.emails.exclude(
            email__in=profile.emails.values_list("email", flat=True)
        ).update(primary=False, profile=profile)

        # Move all affiliations to the "new" profile
        profile_old.affiliations.all().update(profile=profile)

        # Move all SubmissionAuthorProfile instances to the "new" profile
        profile_old.submissionauthorprofile_set.all().update(profile=profile)

        # Move all PublicationAuthorsTable instances to the "new" profile
        profile_old.publicationauthorstable_set.all().update(profile=profile)

        # Move all invitations to the "new" profile
        profile_old.refereeinvitation_set.all().update(profile=profile)
        profile_old.registrationinvitation_set.all().update(profile=profile)

        # Move all PotentialFellowships to the "new" profile
        profile_old.potentialfellowship_set.all().update(profile=profile)

        profile_old.delete()
        return Profile.objects.get(
            id=profile.id
        )  # Retrieve again because of all the db updates.


class ProfileEmailForm(forms.ModelForm):
    class Meta:
        model = ProfileEmail
        fields = ["email", "still_valid", "primary"]

    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop("profile", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """Check if profile/email combination exists."""
        email = self.cleaned_data["email"]
        if self.profile.emails.filter(email=email).exists():
            self.add_error("email", "This profile/email pair is already defined.")
        return email

    def save(self):
        """Save to a profile."""
        if self.cleaned_data["primary"]:
            self.profile.emails.update(primary=False)
        self.instance.profile = self.profile
        return super().save()


class ProfileSelectForm(forms.Form):
    profile = forms.ModelChoiceField(
        queryset=Profile.objects.all(),
        widget=autocomplete.ModelSelect2(url="/profiles/profile-autocomplete"),
        help_text=("Start typing, and select from the popup."),
    )


class ProfileDynSelForm(forms.Form):
    q = forms.CharField(
        max_length=32,
        label="Search (by name, mail, or ORCID); split terms by space, e.g. Abe Cee",
    )
    action_url_name = forms.CharField()
    action_url_base_kwargs = forms.JSONField(required=False)
    action_target_element_id = forms.CharField()
    action_target_swap = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            FloatingField("q", autocomplete="off"),
            Field("action_url_name", type="hidden"),
            Field("action_url_base_kwargs", type="hidden"),
            Field("action_target_element_id", type="hidden"),
            Field("action_target_swap", type="hidden"),
        )

    def search_results(self):
        if self.cleaned_data["q"]:
            splitwords = self.cleaned_data["q"].replace(",", "").split(" ")

            # Get ORCID term.
            orcid_term = Q()
            for i, w in enumerate(splitwords):
                if re.match(r"[\d-]+", w):
                    splitwords.pop(i)
                    orcid_term |= Q(orcid_id__icontains=w)

            # Get mail term.
            mail_term = Q()
            for i, w in enumerate(splitwords):
                if "@" in w:
                    splitwords.pop(i)  # Remove mail from further processing.
                    mail_term |= Q(emails__email__icontains=w)

            base_query = mail_term & orcid_term

            exact_query = base_query
            exact_last_query = base_query
            exact_first_query = base_query
            contains_query = base_query

            for w in splitwords:
                # Find exact matches first where every word matches either first or last name.
                exact_query &= Q(first_name__iexact=w) | Q(last_name__iexact=w)

                # Find an exact match for the last name.
                exact_last_query &= Q(first_name__icontains=w) | Q(last_name__iexact=w)

                # Find an exact match for the first name.
                exact_first_query &= Q(first_name__iexact=w) | Q(last_name__icontains=w)

                # Find a contains match for the last name.
                contains_query &= Q(first_name__icontains=w) | Q(last_name__icontains=w)

            # If there are exact matches, do not include other matches.
            exact_profiles = Profile.objects.filter(exact_query).distinct().distinct()
            if exact_profiles.count() > 0:
                return exact_profiles

            # If there are partial exact matches, do not include other matches.
            exact_first_profiles = Profile.objects.filter(exact_first_query)
            exact_last_profiles = Profile.objects.filter(exact_last_query)
            partial_exact_profiles = (
                exact_first_profiles | exact_last_profiles
            ).distinct()
            if partial_exact_profiles.count() > 0:
                return partial_exact_profiles

            # Include profiles matching all (partial) words in either first or last name.
            contains_profiles = Profile.objects.filter(contains_query).distinct()
            return contains_profiles
        else:
            return Profile.objects.none()


class AffiliationForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
    )

    class Meta:
        model = Affiliation
        fields = [
            "profile",
            "organization",
            "category",
            "description",
            "date_from",
            "date_until",
        ]
        widgets = {
            "profile": forms.HiddenInput(),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_until": forms.DateInput(attrs={"type": "date"}),
        }
