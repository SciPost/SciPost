__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django import forms

from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from django.utils import timezone

from dal import autocomplete
from guardian.shortcuts import assign_perm

from .constants import ORGANIZATION_TYPES, ROLE_GENERAL
from .models import Organization, OrganizationEvent, ContactPerson, Contact, ContactRole

from scipost.constants import TITLE_CHOICES

from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Div, Field, Submit


class SelectOrganizationForm(forms.Form):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        label="",
    )


class OrganizationForm(forms.ModelForm):
    parent = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        label="Parent",
        required=False,
    )
    superseded_by = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        label="Superseded by",
        required=False,
    )
    ror_id = forms.CharField(
        label="ROR ID",
        required=False,
        help_text="Provide the ROR ID of the organization if available, and optionally pre-fill the form with the fetched data.",
        widget=forms.TextInput(attrs={"placeholder": "e.g. https://ror.org/00e5k0821"}),
    )
    orgtype = forms.ChoiceField(
        label="Type",
        choices=ORGANIZATION_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Organization
        fields = [
            "name",
            "name_original",
            "acronym",
            "orgtype",
            "status",
            "logo",
            "country",
            "address",
            "parent",
            "superseded_by",
            "ror_json",
        ]
        widgets = {
            "status": forms.RadioSelect,
            "address": forms.Textarea(attrs={"rows": 1}),
            "ror_json": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.ror_json:
            self.fields["ror_id"].initial = self.instance.ror_json.get("ror_link", "")

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("ror_json")),
                Div(Field("ror_id"), css_class="col"),
                Div(
                    Submit(
                        "fetch_ror",
                        "Fetch Data",
                        css_class="btn btn-primary",
                        formnovalidate="formnovalidate",
                    ),
                    css_class="col-auto mt-4",
                ),
                css_class="row",
            ),
            Div(
                "Names",
                Div(Field("name"), css_class="col"),
                Div(Field("name_original"), css_class="col"),
                Div(Field("acronym"), css_class="col"),
                css_class="row",
            ),
            Div(
                "Classification",
                Div(
                    Field("orgtype"),
                    Field("logo"),
                    css_class="col",
                ),
                Div(Field("status"), css_class="col"),
                css_class="row",
            ),
            Div(
                "Location",
                Div(Field("address"), css_class="col"),
                Div(Field("country"), css_class="col"),
                css_class="row",
            ),
            Div(
                "Relationships",
                Div(Field("parent"), css_class="col"),
                Div(Field("superseded_by"), css_class="col"),
                css_class="row",
            ),
            Submit("submit", "Save"),
        )

    def clean_ror_id(self):
        ror_id = self.cleaned_data["ror_id"]
        if ror_id and not ror_id.startswith("https://ror.org/"):
            raise forms.ValidationError("The ROR ID must start with 'https://ror.org/'")

        if org := (
            Organization.objects.exclude(id=self.instance.id)
            .filter(ror_json__ror_link=ror_id)
            .first()
        ):
            raise forms.ValidationError(
                f"This ROR ID is already in use by {org.name} ({org.get_absolute_url()})."
            )
        return ror_id


class OrganizationEventForm(forms.ModelForm):
    class Meta:
        model = OrganizationEvent
        fields = ["organization", "event", "comments", "noted_on", "noted_by"]


class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = ContactPerson
        fields = "__all__"
        widgets = {
            "date_deprecated": forms.DateInput(attrs={"type": "date"}),
            "info_source": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date_deprecated = cleaned_data.get("date_deprecated")
        status = cleaned_data.get("status")

        if status == ContactPerson.STATUS_DEPRECATED and not date_deprecated:
            self.add_error("date_deprecated", "A deprecation date is required.")
        elif status != ContactPerson.STATUS_DEPRECATED and date_deprecated:
            self.add_error("status", "Status must be set to 'Deprecated'.")

        return cleaned_data

    def clean_email(self):
        """
        Check if the email is already associated to an existing ContactPerson or Contact.
        """
        email = self.cleaned_data["email"]
        try:
            ContactPerson.objects.get(email=email)
            if self.instance.pk:
                pass  # OK, this is an update
            else:
                self.add_error(
                    "email", "This email is already associated to a Contact Person."
                )
        except ContactPerson.DoesNotExist:
            pass
        try:
            Contact.objects.get(user__email=email)
            self.add_error("email", "This email is already associated to a Contact.")
        except Contact.DoesNotExist:
            pass
        return email


class UpdateContactDataForm(forms.ModelForm):
    """
    This form is used in the scipost:update_personal_data method.
    """

    class Meta:
        model = Contact
        fields = ["title"]


class ContactForm(forms.ModelForm):
    """
    This Contact form is mainly used for editing Contact instances.
    """

    class Meta:
        model = Contact
        fields = ["title", "key_expires"]


class NewContactForm(ContactForm):
    """
    This Contact form is used to create new Contact instances, as it will also handle
    possible sending and activation of User instances coming with the new Contact.
    """

    title = forms.ChoiceField(choices=TITLE_CHOICES, label="Title")
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.CharField()
    status = forms.ChoiceField(
        choices=ContactPerson.STATUS_CHOICES, initial=ContactPerson.STATUS_UNKNOWN
    )
    date_deprecated = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    existing_user = None

    def __init__(self, *args, **kwargs):
        """
        Organization is a required argument to tell the formset which Organization
        the Contact is being edited for in the current form.
        """
        self.organization = kwargs.pop("organization")
        self.contactperson = kwargs.pop("contactperson")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """
        Check if User already is known in the system.
        """
        email = self.cleaned_data["email"]
        try:
            self.existing_user = User.objects.get(email=email)
            if not self.data.get("confirm_use_existing", "") == "on":
                # Do not give error if user wants to use existing User
                self.add_error("email", "This User is already registered.")
            self.fields["confirm_use_existing"] = forms.BooleanField(
                required=False,
                initial=False,
                label="Use the existing user instead: %s %s"
                % (self.existing_user.first_name, self.existing_user.last_name),
            )
        except User.DoesNotExist:
            pass
        return email

    @transaction.atomic
    def save(self, current_user, commit=True):
        """
        If existing user is found, link it to the Organization.
        """
        if self.existing_user and self.data.get("confirm_use_existing", "") == "on":
            # Create new Contact if it doesn't already exist
            try:
                contact = self.existing_user.org_contact
            except Contact.DoesNotExist:
                contact = super().save(commit=False)
                contact.title = self.existing_user.org_contact.title
                contact.user = self.existing_user
                contact.save()
            # Assign permissions and Group
            assign_perm("can_view_org_contacts", contact.user, self.organization)
            orgcontacts = Group.objects.get(name="Organization Contacts")
            contact.user.groups.add(orgcontacts)
        else:
            # Create complete new Account (User + Contact)
            user = User(
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                email=self.cleaned_data["email"],
                username=self.cleaned_data["email"],
                is_active=False,
            )
            user.save()
            contact = Contact(user=user, title=self.cleaned_data["title"])
            contact.generate_key()
            contact.save()

            # Assign permissions and Group
            assign_perm("can_view_org_contacts", user, self.organization)
            for child in self.organization.children.all():
                assign_perm("can_view_org_contacts", user, child)
            orgcontacts = Group.objects.get(name="Organization Contacts")
            user.groups.add(orgcontacts)

        # Create the role with to-be-updated info
        contactrole = ContactRole(
            contact=contact,
            organization=self.organization,
            kind=[
                ROLE_GENERAL,
            ],
            date_from=timezone.now(),
            date_until=timezone.now() + datetime.timedelta(days=3650),
        )
        contactrole.save()

        # If upgrading from a ContactPerson, delete the latter
        if self.contactperson:
            self.contactperson.delete()

        return contact


class ContactActivationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = []

    password_new = forms.CharField(label="* Password", widget=forms.PasswordInput())
    password_verif = forms.CharField(
        label="* Verify password",
        widget=forms.PasswordInput(),
        help_text="Your password must contain at least 8 characters",
    )

    def clean(self, *args, **kwargs):
        try:
            self.instance.org_contact
        except Contact.DoesNotExist:
            self.add_error(
                None, "Your account is invalid, please contact the administrator."
            )
        return super().clean(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password_new", "")
        try:
            validate_password(password, self.instance)
        except ValidationError as error_message:
            self.add_error("password_new", error_message)
        return password

    def clean_password_verif(self):
        if self.cleaned_data.get("password_new", "") != self.cleaned_data.get(
            "password_verif", ""
        ):
            self.add_error("password_verif", "Your password entries must match")
        return self.cleaned_data.get("password_verif", "")

    @transaction.atomic
    def activate_user(self):
        if self.errors:
            return forms.ValidationError

        # Activate account
        self.instance.is_active = True
        self.instance.set_password(self.cleaned_data["password_new"])
        self.instance.save()

        return self.instance


class ContactRoleForm(forms.ModelForm):
    class Meta:
        model = ContactRole
        fields = "__all__"
        widgets = {
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["organization"].disabled = True
            self.fields["contact"].disabled = True


class RORSearchForm(forms.Form):
    query = forms.CharField(
        label="Query",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. SciPost Foundation"}),
    )

    def __init__(self, *args, **kwargs):
        self.query = kwargs.pop("query", None)
        super().__init__(*args, **kwargs)
        self.fields["query"].widget.attrs.update({"autofocus": "autofocus"})
        self.fields["query"].initial = self.query

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("query"), css_class="col mb-0"),
                css_class="row",
            ),
        )
