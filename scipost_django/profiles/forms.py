__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import reduce
import re
from django import forms
from django.db.models import Q, Exists, OuterRef

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, Submit, Button, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete
from django.forms import ChoiceField
from django.urls import reverse

from colleges.models.fellowship import Fellowship
from common.forms import ModelChoiceFieldwithid
from invitations.models import RegistrationInvitation
from ontology.models.specialty import Specialty
from ontology.models.topic import Topic
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
            "first_name_original",
            "last_name_original",
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
        widgets = {
            "specialties": autocomplete.ModelSelect2Multiple(
                url="/ontology/specialty-autocomplete",
                attrs={"data-html": True},
            ),
            "topics": autocomplete.ModelSelect2Multiple(
                url="/ontology/topic-autocomplete",
                attrs={"data-html": True},
                forward=["specialties"],
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["instance_from_type"].widget = forms.HiddenInput()
        self.fields["instance_pk"].widget = forms.HiddenInput()

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("title"), css_class="col-12 col-md-3"),
                Div(Field("first_name"), css_class="col-12 col-md"),
                Div(Field("last_name"), css_class="col-12 col-md"),
                css_class="row mb-0",
            ),
            Div(
                Div(
                    Div(Field("accepts_SciPost_emails")),
                    Div(Field("accepts_refereeing_requests")),
                    css_class="col-12 col-md-3 d-flex flex-column gap-2",
                ),
                Div(Field("first_name_original"), css_class="col-12 col-md"),
                Div(Field("last_name_original"), css_class="col-12 col-md"),
                css_class="row mb-0",
            ),
            Div(
                Div(Field("acad_field"), css_class="col-12 col-md-3"),
                Div(Field("specialties"), css_class="col-12 col-md"),
                Div(Field("topics"), css_class="col-12 col-md"),
                css_class="row mb-0",
            ),
            Div(
                Div(Field("orcid_id"), css_class="col-12 col-md-3"),
                Div(Field("email"), css_class="col-12 col-md"),
                Div(Field("webpage"), css_class="col-12 col-md"),
                css_class="row mb-0",
            ),
            Div(
                Submit("submit", "Save", css_class="btn btn-primary"),
            ),
        )

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
        if email := self.cleaned_data["email"]:
            profile_email, _ = ProfileEmail.objects.get_or_create(
                profile=profile,
                email=email,
                defaults={"still_valid": True},
            )
            profile_email.set_primary()

        instance_pk = self.cleaned_data["instance_pk"]
        if instance_pk:
            if self.cleaned_data["instance_from_type"] == "contributor":
                Contributor.objects.filter(pk=instance_pk).update(profile=profile)
            elif self.cleaned_data["instance_from_type"] == "refereeinvitation":
                RefereeInvitation.objects.filter(pk=instance_pk).update(referee=profile)
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
        queryset=Profile.objects.none(),
        empty_label=None,
        label="Merge this profile",
    )
    to_merge_into = ModelChoiceFieldwithid(
        queryset=Profile.objects.none(),
        empty_label=None,
        label="into this profile",
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop("queryset", Profile.objects.all())
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
        to_merge: Profile | None = data.get("to_merge")
        to_merge_into: Profile | None = data.get("to_merge_into")

        if to_merge is None or to_merge_into is None:
            raise forms.ValidationError("Both profiles must be selected.")

        if to_merge == to_merge_into:
            self.add_error(None, "A Profile cannot be merged into itself.")
        if to_merge.has_active_contributor and to_merge_into.has_active_contributor:
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
        profile: "Profile" = self.cleaned_data["to_merge_into"]
        profile_old: "Profile" = self.cleaned_data["to_merge"]

        # Merge information from old to new Profile.
        if profile.orcid_id is None:
            profile.orcid_id = profile_old.orcid_id
            profile_old.orcid_id = None
        if profile.webpage == "":
            profile.webpage = profile_old.webpage
        if profile.acad_field is None:
            profile.acad_field = profile_old.acad_field
        if profile_old.has_active_contributor and not profile.has_active_contributor:
            profile.contributor = profile_old.contributor

        profile_old.save()  # Purge old Profile data.
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
        profile_old.referee_invitations.all().update(referee=profile)
        profile_old.registrationinvitation_set.all().update(profile=profile)
        profile_old.editorial_communications.all().update(referee=profile)

        # Move all PotentialFellowships to the "new" profile
        profile_old.potentialfellowship_set.all().update(profile=profile)

        # Move all RedFlags to the "new" profile
        profile.red_flags.add(*profile_old.red_flags.all())

        # Move all Nomination instances to the "new" profile
        profile.fellowship_nominations.add(*profile_old.fellowship_nominations.all())

        profile_old.delete()
        return Profile.objects.get(
            id=profile.id
        )  # Retrieve again because of all the db updates.


class AddProfileEmailForm(forms.ModelForm):
    class Meta:
        model = ProfileEmail
        fields = ["email"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.profile = kwargs.pop("profile", None)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    FloatingField("email", type="email", placeholder="Email address"),
                    css_class="col",
                ),
                Div(
                    ButtonHolder(
                        Submit("submit", "Add", css_class="btn btn-sm btn-primary"),
                        Button(
                            "cancel",
                            "Cancel",
                            css_class="btn btn-sm btn-secondary",
                            hx_get=reverse("common:empty"),
                            hx_target="closest " + kwargs.pop("cancel_parent_tag", "*"),
                            hx_swap="outerHTML",
                        ),
                        css_class="d-flex flex-column justify-content-between",
                    ),
                    css_class="col-auto",
                ),
                css_class="row",
            ),
        )
        self.helper.attrs |= kwargs.pop("hx_attrs", {})

        super().__init__(*args, **kwargs)

    def clean_email(self):
        """Check if profile/email combination exists."""
        email = self.cleaned_data["email"]
        if self.profile.emails.filter(email=email).exists():
            self.add_error("email", "This profile/email pair is already defined.")
        return email

    def save(self):
        """Mark the email as still_valid but not primary."""

        self.instance.profile = self.profile
        self.instance.still_valid = True
        self.instance.primary = False
        self.instance.added_by = self.request.user.contributor if self.request else None
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
            return Profile.objects.search(self.cleaned_data["q"]).annotate(
                is_fellow=Exists(
                    Fellowship.objects.filter(
                        Q(contributor__profile=OuterRef("id"))
                    ).active()
                )
            )
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
