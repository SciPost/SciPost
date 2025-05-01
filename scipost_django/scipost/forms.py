__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import bleach
from django.db.models import Q
from django.utils.html import format_html
import pyotp
import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from dal import autocomplete

from common.utils.text import split_strip
from markup.constants import BLEACH_ALLOWED_ATTRIBUTES, BLEACH_ALLOWED_TAGS

from .behaviors import orcid_validator
from .constants import (
    NEWLY_REGISTERED,
    NORMAL_CONTRIBUTOR,
    TITLE_CHOICES,
    SCIPOST_FROM_ADDRESSES,
    UNVERIFIABLE_CREDENTIALS,
    NO_SCIENTIST,
    DOUBLE_ACCOUNT,
    BARRED,
)
from .fields import ReCaptchaField
from .models import (
    Contributor,
    UnavailabilityPeriod,
    Remark,
    AuthorshipClaim,
    PrecookedEmail,
    TOTPDevice,
)
from .totp import TOTPVerification

from common.forms import ModelChoiceFieldwithid, MultiEmailField

from colleges.models import Fellowship, PotentialFellowshipEvent
from commentaries.models import Commentary
from comments.models import Comment
from common.utils import get_current_domain
from funders.models import Grant
from invitations.models import CitationNotification
from journals.models import PublicationAuthorsTable, Publication
from mails.utils import DirectMailUtil
from ontology.models import AcademicField, Specialty
from organizations.models import Organization
from profiles.models import Profile, ProfileEmail, Affiliation
from submissions.models import (
    Submission,
    EditorialAssignment,
    RefereeInvitation,
    Report,
    EditorialCommunication,
    EICRecommendation,
)
from theses.models import ThesisLink

domain = get_current_domain()

REGISTRATION_REFUSAL_CHOICES = (
    (None, "-"),
    (UNVERIFIABLE_CREDENTIALS, "unverifiable credentials"),
    (NO_SCIENTIST, "not a professional scientist (>= PhD student)"),
    (DOUBLE_ACCOUNT, "another account already exists for this person"),
    (BARRED, "barred from SciPost (abusive behaviour)"),
)
reg_ref_dict = dict(REGISTRATION_REFUSAL_CHOICES)


class RequestFormMixin:
    """
    This mixin lets the Form accept `request` as an argument.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)


class HttpRefererFormMixin(RequestFormMixin):
    """
    This mixin adds a HiddenInput to the form which tracks the previous url, which can
    be used to redirect to.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["http_referer"] = forms.URLField(
            widget=forms.HiddenInput(), required=False
        )
        if self.request:
            self.fields["http_referer"].initial = self.request.headers.get("referer")


class RegistrationForm(forms.Form):
    """
    Use this form to process the registration of new accounts.
    Due to the construction of a separate Contributor from the User,
    it is difficult to create a 'combined ModelForm'. All fields
    are thus separately handled here.
    """

    required_css_class = "required-asterisk"

    title = forms.ChoiceField(choices=TITLE_CHOICES, label="Title")
    email = forms.EmailField(label="Email address")
    first_name = forms.CharField(label="First name", max_length=64)
    last_name = forms.CharField(label="Last name", max_length=64)
    first_name_original = forms.CharField(
        label="First name (original script)",
        max_length=64,
        required=False,
        help_text="Name in original script (if not using the Latin alphabet)",
    )
    last_name_original = forms.CharField(
        label="Last name (original script)",
        max_length=64,
        required=False,
        help_text="Name in original script (if not using the Latin alphabet)",
    )
    invitation_key = forms.CharField(
        max_length=40, widget=forms.HiddenInput(), required=False
    )
    orcid_id = forms.CharField(
        label="ORCID id",
        max_length=20,
        required=False,
        validators=[orcid_validator],
        widget=forms.TextInput({"placeholder": "Recommended. Get one at orcid.org"}),
    )
    acad_field = forms.ModelChoiceField(
        queryset=AcademicField.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/ontology/acad_field-autocomplete?exclude=multidisciplinary"
        ),
        label="Academic field",
        help_text="Your main field of activity",
        required=False,
    )
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        help_text="Type to search, click to include",
        required=False,
    )
    current_affiliation = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/organizations/organization-autocomplete", attrs={"data-html": True}
        ),
        label="Current affiliation",
        help_text=(
            "Start typing, then select in the popup; "
            "if you do not find the organization you seek, "
            "please fill in your institution name and address instead."
        ),
        required=False,
    )
    address = forms.CharField(
        label="Institution name and address",
        max_length=1000,
        widget=forms.TextInput(
            {"placeholder": "[only if you did not find your affiliation above]"}
        ),
        required=False,
    )
    webpage = forms.URLField(
        label="Personal web page",
        required=False,
        widget=forms.TextInput(
            {"placeholder": "full URL, e.g. https://www.[yourpage].com"}
        ),
    )
    username = forms.CharField(
        label="Username",
        max_length=100,
        validators=[
            UnicodeUsernameValidator,
        ],
    )
    password = forms.CharField(label="Password", widget=forms.PasswordInput())
    password_verif = forms.CharField(
        label="Verify password",
        widget=forms.PasswordInput(),
        help_text="Your password must contain at least 8 characters",
    )
    captcha = ReCaptchaField(label="Please verify to continue:")
    subscribe = forms.BooleanField(
        required=False,
        initial=False,
        label="Stay informed, subscribe to the SciPost newsletter.",
    )

    def clean(self):
        """
        Check that:
        * either an organization or an address are provided
        * that any existing associated profile does not already have a Contributor
        """
        cleaned_data = super(RegistrationForm, self).clean()
        current_affiliation = cleaned_data.get("current_affiliation", None)
        address = cleaned_data.get("address", "")

        if current_affiliation is None and address == "":
            raise forms.ValidationError(
                "You must either specify a Current Affiliation, or "
                "fill in the institution name and address field"
            )

        profile = Profile.objects.filter(
            emails__email__iexact=self.cleaned_data["email"]
        ).first()
        try:
            if profile and profile.contributor:
                raise forms.ValidationError(
                    "There is already a registered Contributor with your email address. "
                    f"Please contact techsupport@{domain} to clarify this issue."
                )
        except Contributor.DoesNotExist:
            pass

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        user = User(
            username=self.cleaned_data.get("username", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            email=self.cleaned_data.get("email", ""),
        )
        try:
            validate_password(password, user)
        except ValidationError as error_message:
            self.add_error("password", error_message)
        return password

    def clean_password_verif(self):
        if self.cleaned_data.get("password", "") != self.cleaned_data.get(
            "password_verif", ""
        ):
            self.add_error("password_verif", "Your password entries must match")
        return self.cleaned_data.get("password_verif", "")

    def clean_username(self):
        # Username should not contain spaces or special characters
        username = self.cleaned_data.get("username", "")
        if re.search(r"[^a-zA-Z0-9._@\-+]", username):
            raise forms.ValidationError(
                "Your username may only contain letters, numbers, and any of the following: . _ @ - +"
            )

        if User.objects.filter(username=username).exists():
            self.add_error("username", "This username is already in use")
        return username

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data["email"]).exists():
            self.add_error("email", "This email address is already in use")
        return self.cleaned_data.get("email", "")

    def clean_orcid_id(self):
        orcid_id = self.cleaned_data.get("orcid_id", "")
        if orcid_id and Profile.objects.filter(orcid_id=orcid_id).exists():
            error_message = format_html(
                "This ORCID id is already in use. Have you already registered?"
                "<a href='/password_reset/'>Reset your password</a> or "
                "<a href='mailto:techsupport@scipost.org'>contact tech support</a>."
            )
            self.add_error("orcid_id", error_message)
        return orcid_id

    def create_and_save_contributor(self):
        user = User.objects.create_user(
            **{
                "first_name": self.cleaned_data["first_name"],
                "last_name": self.cleaned_data["last_name"],
                "email": self.cleaned_data["email"],
                "username": self.cleaned_data["username"],
                "password": self.cleaned_data["password"],
                "is_active": False,
            }
        )

        profile = Profile.objects.create(
            title=self.cleaned_data["title"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            first_name_original=self.cleaned_data["first_name_original"],
            last_name_original=self.cleaned_data["last_name_original"],
            acad_field=self.cleaned_data["acad_field"],
            orcid_id=self.cleaned_data["orcid_id"] or None,
            webpage=self.cleaned_data["webpage"],
        )
        profile.specialties.set(self.cleaned_data["specialties"])
        # Add a ProfileEmail to this Profile
        ProfileEmail.objects.create(
            profile=profile,
            primary=True,
            email=self.cleaned_data["email"],
        )
        # Create an Affiliation for this Profile
        current_affiliation = self.cleaned_data.get("current_affiliation", None)
        if current_affiliation:
            Affiliation.objects.create(
                profile=profile, organization=self.cleaned_data["current_affiliation"]
            )
        # Create the Contributor object
        contributor, __ = Contributor.objects.get_or_create(
            **{
                "profile": profile,
                "user": user,
                "invitation_key": self.cleaned_data.get("invitation_key", ""),
                "address": self.cleaned_data["address"],
            }
        )
        contributor.save()

        # Automatically vet the Contributor if they have an invitation key
        if contributor.invitation_key:
            contributor.status = NORMAL_CONTRIBUTOR
            contributor.save()
            group = Group.objects.get(name="Registered Contributors")
            contributor.user.groups.add(group)
            contributor.user.is_active = True
            contributor.user.save()

        return contributor


class ModifyPersonalMessageForm(forms.Form):
    personal_message = forms.CharField(widget=forms.Textarea())


class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["last_name"].widget.attrs["readonly"] = True

    def clean_email(self):
        # Guard against empty email address
        if not (email := self.cleaned_data.get("email")):
            raise ValidationError("The email address cannot be empty.")

        other_users = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if other_users.exists():
            raise ValidationError(
                "This email is already in use by another user. "
                "If it belongs to you and you have forgotten your credentials, "
                "use the email in place of your username and/or reset your password.",
            )

        profile_email, created = ProfileEmail.objects.get_or_create(
            email=email, profile=self.instance.contributor.profile
        )

        # If just created, it needs to be verified
        if created:
            profile_email.send_verification_email()
            raise ValidationError(
                "This email is not yet verified. Please check your inbox for a verification email."
            )
        # Existing, but of another User
        elif profile_email.profile.contributor != self.instance.contributor:
            raise ValidationError(
                "This email is already declared as belonging to another person. "
                "Please contact tech support.",
            )
        # Existing, of this User, but not verified
        elif not profile_email.verified:
            profile_email.send_verification_email()
            raise ValidationError(
                "This email is not yet verified. Please check your inbox for a verification email."
            )

        # Existing, of this User, and verified
        profile_email.set_primary()
        return email

    def clean_last_name(self):
        """Make sure the `last_name` cannot be saved via this form."""
        instance = getattr(self, "instance", None)
        if instance and instance.last_name:
            return instance.last_name
        else:
            return self.cleaned_data["last_name"]


class UpdatePersonalDataForm(forms.ModelForm):
    title = forms.ChoiceField(choices=TITLE_CHOICES, label="* Title")
    acad_field = forms.ModelChoiceField(
        queryset=AcademicField.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="/ontology/acad_field-autocomplete?exclude=multidisciplinary"
        ),
        label="Academic field",
        help_text="Your main field of activity",
        required=False,
    )
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/ontology/specialty-autocomplete", attrs={"data-html": True}
        ),
        label="Specialties",
        help_text="Type to search, click to include",
        required=False,
    )
    orcid_id = forms.CharField(
        label="ORCID id",
        max_length=20,
        required=False,
        validators=[orcid_validator],
        widget=forms.TextInput({"placeholder": "Recommended. Get one at orcid.org"}),
    )
    webpage = forms.URLField(
        label="Personal web page",
        required=False,
        widget=forms.TextInput(
            {"placeholder": "full URL, e.g. https://[yourpage].org"}
        ),
    )

    class Meta:
        model = Contributor
        fields = [
            "title",
            "acad_field",
            "specialties",
            "orcid_id",
            "address",
            "webpage",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].initial = self.instance.profile.title
        if self.instance.profile.acad_field:
            self.fields["acad_field"].initial = self.instance.profile.acad_field.id
        self.fields["specialties"].initial = [
            s.id for s in self.instance.profile.specialties.all()
        ]
        self.fields["orcid_id"].initial = self.instance.profile.orcid_id
        self.fields["webpage"].initial = self.instance.profile.webpage

    def save(self):
        self.instance.profile.title = self.cleaned_data["title"]
        self.instance.profile.acad_field = self.cleaned_data["acad_field"]
        if self.cleaned_data["orcid_id"] != self.instance.profile.orcid_id:
            self.instance.profile.orcid_authenticated = False
        self.instance.profile.orcid_id = self.cleaned_data["orcid_id"] or None
        self.instance.profile.webpage = self.cleaned_data["webpage"]
        self.instance.profile.save()
        self.instance.profile.specialties.set(self.cleaned_data["specialties"])
        return super().save()

    def clean_orcid_id(self):
        if (
            orcid_id := self.cleaned_data.get("orcid_id", "")
        ) and Profile.objects.filter(orcid_id=orcid_id).exclude(
            id=self.instance.profile.id
        ).exists():
            error_message = format_html(
                "This ORCID id is already in use by another member. Is it yours? "
                "<a href='mailto:techsupport@scipost.org'>Contact tech support</a>."
            )
            self.add_error("orcid_id", error_message)
        return orcid_id

    def sync_lists(self):
        """
        Pseudo U/S; do not remove
        """
        return

    def propagate_orcid(self):
        """
        This method is called if a Contributor updates their personal data,
        and changes the orcid_id. It marks all Publications, Reports and Comments
        authored by this Contributor with a deposit_requires_update == True.
        """
        publications = Publication.objects.filter(
            authors__profile=self.instance.profile
        )
        for publication in publications:
            publication.doideposit_needs_updating = True
            publication.save()
        reports = Report.objects.filter(author=self.instance, anonymous=False)
        for report in reports:
            report.doideposit_needs_updating = True
            report.save()
        comments = Comment.objects.filter(author=self.instance, anonymous=False)
        for comment in comments:
            comment.doideposit_needs_updating = True
            comment.save()
        return


class VetRegistrationForm(forms.Form):
    decision = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Accept registration"), (False, "Refuse")),
    )
    refusal_reason = forms.ChoiceField(
        choices=REGISTRATION_REFUSAL_CHOICES, required=False
    )
    email_response_field = forms.CharField(
        widget=forms.Textarea(), label="Justification (optional)", required=False
    )

    def promote_to_registered_contributor(self):
        return self.cleaned_data.get("decision") == "True"


class SciPostAuthenticationForm(AuthenticationForm):
    """
    Authentication form for all types of users at SciPost.

    Inherits from django.contrib.auth.forms:AuthenticationForm.

    Extra fields:

    * next: url for the next page, obtainable via POST

    Overriden methods:

    * clean: allow either username, or email as substitute for username
    * confirm_login_allowed: disallow inactive or unvetted accounts.
    """

    next = forms.CharField(widget=forms.HiddenInput(), required=False)
    code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        help_text="Please type in the code displayed on your authenticator app from your device",
    )

    def clean(self):
        """Allow either username, or email as substitute for username."""
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                try:
                    _user = User.objects.get(email=username)
                    self.user_cache = authenticate(
                        self.request, username=_user.username, password=password
                    )
                except:
                    pass
            if self.user_cache is None:
                raise forms.ValidationError(
                    (
                        "Please enter a correct %(username)s and password. "
                        "Note that both fields may be case-sensitive. "
                        "Your can use your email instead of your username."
                    ),
                    code="invalid_login",
                    params={"username": self.username_field.verbose_name},
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                (
                    "Your account is not yet activated. "
                    "Please first activate your account by clicking on the "
                    "activation link we emailed you."
                ),
                code="inactive",
            )
        if not user.groups.exists():
            raise forms.ValidationError(
                (
                    "Your account has not yet been vetted.\n"
                    "Our admins will verify your credentials very soon, "
                    "and if vetted (your will receive an information email) "
                    "you will then be able to login."
                ),
                code="unvetted",
            )
        if user.devices.exists():
            if self.cleaned_data.get("code"):
                code = self.cleaned_data.get("code")
                totp = TOTPVerification(user)
                if not totp.verify_code(code):
                    self.add_error("code", "Invalid code")
            else:
                self.add_error("code", "Your account uses two factor authentication")


class UserAuthInfoForm(forms.Form):
    username = forms.CharField()

    def get_data(self):
        username = self.cleaned_data.get("username")
        return {
            "username": username,
            "has_password": True,
            "has_totp": TOTPDevice.objects.filter(user__username=username).exists(),
        }


class TOTPDeviceForm(forms.ModelForm):
    code = forms.CharField(
        required=True,
        help_text=(
            "Enter the security code generated by your mobile authenticator"
            " app to make sure it’s configured correctly."
        ),
    )

    class Meta:
        model = TOTPDevice
        fields = ["name", "token"]
        widgets = {"token": forms.HiddenInput()}
        labels = {"name": "Device name"}

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user")
        super().__init__(*args, **kwargs)
        self.initial["token"] = pyotp.random_base32()
        self.fields["name"].widget.attrs.update(
            {"placeholder": "Your choice of a simple memorable name for your device"}
        )

    @property
    def secret_key(self):
        if hasattr(self, "cleaned_data") and "token" in self.cleaned_data:
            return self.cleaned_data.get("token")
        return self.initial["token"]

    def get_QR_data(self):
        return pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            self.current_user.email, issuer_name="SciPost"
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        code = cleaned_data.get("code")
        token = cleaned_data.get("token")
        if not TOTPVerification.verify_token(token, code):
            self.add_error("code", "Invalid code, please try again.")
        return cleaned_data

    def save(self):
        totp_device = super().save(commit=False)
        totp_device.user = self.current_user
        totp_device.save()
        return totp_device


AUTHORSHIP_CLAIM_CHOICES = (
    ("-", "-"),
    ("True", "I am an author"),
    ("False", "I am not an author"),
)


class AuthorshipClaimForm(forms.Form):
    claim = forms.ChoiceField(choices=AUTHORSHIP_CLAIM_CHOICES, required=False)


class UnavailabilityPeriodForm(forms.ModelForm):
    class Meta:
        model = UnavailabilityPeriod
        fields = ["start", "end"]
        widgets = {
            "start": forms.DateInput(attrs={"type": "date"}),
            "end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("start"), css_class="col"),
                Div(Field("end"), css_class="col"),
                Div(
                    ButtonHolder(
                        Submit("submit", "Submit", css_class="btn btn-primary"),
                    ),
                    css_class="col",
                ),
                css_class="row",
            )
        )

    def clean_end(self):
        now = timezone.now()
        start = self.cleaned_data.get("start")
        end = self.cleaned_data.get("end")
        if not start or not end:
            return end

        if start > end:
            self.add_error(
                "end", "The start date you have entered is later than the end date."
            )

        if end < now.date():
            self.add_error("end", "You have entered an end date in the past.")
        return end


class ContributorMergeForm(forms.Form):
    to_merge = ModelChoiceFieldwithid(
        queryset=Contributor.objects.all(),
        empty_label=None,
        label="Merge this contributor",
    )
    to_merge_into = ModelChoiceFieldwithid(
        queryset=Contributor.objects.all(),
        empty_label=None,
        label="Into this contributor",
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
                "scipost:_hx_contributor_comparison",
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
        data = super().clean()
        if self.cleaned_data["to_merge"] == self.cleaned_data["to_merge_into"]:
            self.add_error(None, "A Contributor cannot be merged into itself.")
        return data

    def save(self):
        """
        Merge one Contributor into another. Set the previous Contributor to inactive.
        """
        contrib_from = self.cleaned_data["to_merge"]
        contrib_into = self.cleaned_data["to_merge_into"]

        both_contribs_active = contrib_from.is_active and contrib_into.is_active

        contrib_from_qs = Contributor.objects.filter(pk=contrib_from.id)
        contrib_into_qs = Contributor.objects.filter(pk=contrib_into.id)

        # Step 1: update all fields within Contributor
        if contrib_from.profile and not contrib_into.profile:
            profile = contrib_from.profile
            contrib_from_qs.update(profile=None)
            contrib_into_qs.update(profile=profile)
        User.objects.filter(pk=contrib_from.user.id).update(is_active=False)
        User.objects.filter(pk=contrib_into.user.id).update(is_active=True)
        if contrib_from.invitation_key and not contrib_into.invitation_key:
            contrib_into_qs.update(invitation_key=contrib_into.invitation_key)
        if contrib_from.activation_key and not contrib_into.activation_key:
            contrib_into_qs.update(activation_key=contrib_into.activation_key)
        contrib_from_qs.update(status=DOUBLE_ACCOUNT)

        # Specify duplicate_of for deactivated Contributor
        contrib_from_qs.update(duplicate_of=contrib_into)

        # Step 2: update all ForeignKey relations
        Fellowship.objects.filter(contributor=contrib_from).update(
            contributor=contrib_into
        )
        PotentialFellowshipEvent.objects.filter(noted_by=contrib_from).update(
            noted_by=contrib_into
        )
        Commentary.objects.filter(requested_by=contrib_from).update(
            requested_by=contrib_into
        )
        Commentary.objects.filter(vetted_by=contrib_from).update(vetted_by=contrib_into)
        Comment.objects.filter(vetted_by=contrib_from).update(vetted_by=contrib_into)
        Comment.objects.filter(author=contrib_from).update(author=contrib_into)
        Grant.objects.filter(recipient=contrib_from).update(recipient=contrib_into)
        CitationNotification.objects.filter(contributor=contrib_from).update(
            contributor=contrib_into
        )
        PublicationAuthorsTable.objects.filter(profile=contrib_from.profile).update(
            profile=contrib_into.profile
        )
        UnavailabilityPeriod.objects.filter(contributor=contrib_from).update(
            contributor=contrib_into
        )
        Remark.objects.filter(contributor=contrib_from).update(contributor=contrib_into)
        AuthorshipClaim.objects.filter(claimant=contrib_from).update(
            claimant=contrib_into
        )
        AuthorshipClaim.objects.filter(vetted_by=contrib_from).update(
            vetted_by=contrib_into
        )
        Submission.objects.filter(editor_in_charge=contrib_from).update(
            editor_in_charge=contrib_into
        )
        Submission.objects.filter(submitted_by=contrib_from).update(
            submitted_by=contrib_into
        )
        EditorialAssignment.objects.filter(to=contrib_from).update(to=contrib_into)
        RefereeInvitation.objects.filter(invited_by=contrib_from).update(
            invited_by=contrib_into
        )
        Report.objects.filter(vetted_by=contrib_from).update(vetted_by=contrib_into)
        Report.objects.filter(author=contrib_from).update(author=contrib_into)
        EditorialCommunication.objects.filter(referee=contrib_from).update(
            referee=contrib_into
        )
        ThesisLink.objects.filter(requested_by=contrib_from).update(
            requested_by=contrib_into
        )
        ThesisLink.objects.filter(vetted_by=contrib_from).update(vetted_by=contrib_into)

        # Step 3: update all ManyToMany
        commentaries = Commentary.objects.filter(
            authors__in=[
                contrib_from,
            ]
        ).all()
        for commentary in commentaries:
            commentary.authors.remove(contrib_from)
            commentary.authors.add(contrib_into)
        commentaries = Commentary.objects.filter(
            authors_claims__in=[
                contrib_from,
            ]
        ).all()
        for commentary in commentaries:
            commentary.authors_claims.remove(contrib_from)
            commentary.authors_claims.add(contrib_into)
        commentaries = Commentary.objects.filter(
            authors_false_claims__in=[
                contrib_from,
            ]
        ).all()
        for commentary in commentaries:
            commentary.authors_false_claims.remove(contrib_from)
            commentary.authors_false_claims.add(contrib_into)
        submissions = Submission.objects.filter(
            authors__in=[
                contrib_from,
            ]
        ).all()
        for submission in submissions:
            submission.authors.remove(contrib_from)
            submission.authors.add(contrib_into)
        submissions = Submission.objects.filter(
            authors_claims__in=[
                contrib_from,
            ]
        ).all()
        for submission in submissions:
            submission.authors_claims.remove(contrib_from)
            submission.authors_claims.add(contrib_into)
        submissions = Submission.objects.filter(
            authors_false_claims__in=[
                contrib_from,
            ]
        ).all()
        for submission in submissions:
            submission.authors_false_claims.remove(contrib_from)
            submission.authors_false_claims.add(contrib_into)
        eicrecs = EICRecommendation.objects.filter(
            eligible_to_vote__in=[
                contrib_from,
            ]
        ).all()
        for eicrec in eicrecs:
            eicrec.eligible_to_vote.remove(contrib_from)
            eicrec.eligible_to_vote.add(contrib_into)
        eicrecs = EICRecommendation.objects.filter(
            voted_for__in=[
                contrib_from,
            ]
        ).all()
        for eicrec in eicrecs:
            eicrec.voted_for.remove(contrib_from)
            eicrec.voted_for.add(contrib_into)
        eicrecs = EICRecommendation.objects.filter(
            voted_against__in=[
                contrib_from,
            ]
        ).all()
        for eicrec in eicrecs:
            eicrec.voted_against.remove(contrib_from)
            eicrec.voted_against.add(contrib_into)
        eicrecs = EICRecommendation.objects.filter(
            voted_abstain__in=[
                contrib_from,
            ]
        ).all()
        for eicrec in eicrecs:
            eicrec.voted_abstain.remove(contrib_from)
            eicrec.voted_abstain.add(contrib_into)
        thesislinks = ThesisLink.objects.filter(
            author_as_cont__in=[
                contrib_from,
            ]
        ).all()
        for tl in thesislinks:
            tl.author_as_cont.remove(contrib_from)
            tl.author_as_cont.add(contrib_into)
        thesislinks = ThesisLink.objects.filter(
            author_claims__in=[
                contrib_from,
            ]
        ).all()
        for tl in thesislinks:
            tl.author_claims.remove(contrib_from)
            tl.author_claims.add(contrib_into)
        thesislinks = ThesisLink.objects.filter(
            author_false_claims__in=[
                contrib_from,
            ]
        ).all()
        for tl in thesislinks:
            tl.author_false_claims.remove(contrib_from)
            tl.author_false_claims.add(contrib_into)
        thesislinks = ThesisLink.objects.filter(
            supervisor_as_cont__in=[
                contrib_from,
            ]
        ).all()
        for tl in thesislinks:
            tl.supervisor_as_cont.remove(contrib_from)
            tl.supervisor_as_cont.add(contrib_into)
        # If both accounts were active, inform the Contributor of the merge
        if both_contribs_active:
            mail_sender = DirectMailUtil(
                "contributors/inform_contributor_duplicate_accounts_merged",
                object=Contributor.objects.get(id=contrib_from.id),
            )
            mail_sender.send_mail()
        return Contributor.objects.get(id=contrib_into.id)


class RemarkForm(forms.Form):
    remark = forms.CharField(widget=forms.Textarea(), label="")

    def __init__(self, *args, **kwargs):
        super(RemarkForm, self).__init__(*args, **kwargs)
        self.fields["remark"].widget.attrs.update(
            {
                "rows": 3,
                "cols": 40,
                "placeholder": "Enter your remarks here. You can use LaTeX in $...$ or \[ \].",
            }
        )


def get_date_filter_choices():
    today = datetime.date.today()
    empty = [(0, "---")]
    months = empty + list(MONTHS.items())
    years = empty + [(i, i) for i in range(today.year - 4, today.year + 1)]
    return months, years


class SearchTextForm(forms.Form):
    """
    Simple text-based search form.
    """

    text = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={"placeholder": "Search", "type": "search", "class": "form-control"}
        ),
    )


class EmailGroupMembersForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all())
    email_subject = forms.CharField(widget=forms.Textarea(), label="")
    personalize = forms.BooleanField(
        required=False, initial=False, label="Personalize (Dear Prof. AAA)?"
    )
    email_text = forms.CharField(widget=forms.Textarea(), label="")
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False, label="include SciPost summary at end of message"
    )

    def __init__(self, *args, **kwargs):
        super(EmailGroupMembersForm, self).__init__(*args, **kwargs)
        self.fields["email_subject"].widget.attrs.update(
            {"rows": 1, "cols": 50, "placeholder": "Email subject"}
        )
        self.fields["email_text"].widget.attrs.update(
            {"rows": 15, "cols": 50, "placeholder": "Write your message in this box."}
        )


class EmailParticularForm(forms.Form):
    email_address = forms.EmailField(label="")
    email_subject = forms.CharField(widget=forms.Textarea(), label="")
    email_text = forms.CharField(widget=forms.Textarea(), label="")
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False, label="Include SciPost summary at end of message"
    )

    def __init__(self, *args, **kwargs):
        super(EmailParticularForm, self).__init__(*args, **kwargs)
        self.fields["email_address"].widget.attrs.update(
            {"placeholder": "Email address"}
        )
        self.fields["email_subject"].widget.attrs.update(
            {"rows": 1, "cols": 50, "placeholder": "Email subject"}
        )
        self.fields["email_text"].widget.attrs.update(
            {"rows": 15, "cols": 50, "placeholder": "Write your message in this box."}
        )


class EmailUsersForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="/user-autocomplete", attrs={"data-html": True}
        ),
        label="Recipients",
        required=True,
    )
    cc_mail_field = MultiEmailField(label="Optional: cc this email to", required=False)
    bcc_mail_field = MultiEmailField(
        label="Optional: bcc this email to", required=False
    )
    email_subject = forms.CharField(widget=forms.Textarea(), label="")
    personalize = forms.BooleanField(
        required=False, initial=False, label="Personalize (Dear Prof. AAA)?"
    )
    email_text = forms.CharField(widget=forms.Textarea(), label="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email_subject"].widget.attrs.update(
            {"rows": 1, "cols": 50, "placeholder": "Email subject"}
        )
        self.fields["email_text"].widget.attrs.update(
            {"rows": 15, "cols": 50, "placeholder": "Write your message in this box."}
        )

    def save(self):
        from django.core import mail
        from django.template import Context, Template

        with mail.get_connection() as connection:
            for user in self.cleaned_data["users"]:
                email_text = ""
                email_text_html = ""
                if self.cleaned_data["personalize"]:
                    email_text = f"Dear {user.contributor.profile.formal_name}, \n\n"
                    email_text_html = "Dear {{ formal_name }},<br/>"

                bleached_email_text = bleach.clean(
                    self.cleaned_data["email_text"],
                    tags=BLEACH_ALLOWED_TAGS,
                    attributes=BLEACH_ALLOWED_ATTRIBUTES,
                )
                email_text += bleached_email_text
                email_text_html += "{{ bleached_email_text|safe|linebreaksbr }}"

                email_context = {
                    "formal_name": user.contributor.profile.formal_name,
                    "bleached_email_text": bleached_email_text,
                }
                html_template = Template(email_text_html)
                html_version = html_template.render(Context(email_context))

                addresses_cc = []
                addresses_bcc = []
                if cc_field := self.cleaned_data.get("cc_mail_field"):
                    addresses_cc = split_strip(cc_field)
                if bcc_field := self.cleaned_data.get("bcc_mail_field"):
                    addresses_bcc = split_strip(bcc_field)

                message = mail.EmailMultiAlternatives(
                    self.cleaned_data["email_subject"],
                    email_text,
                    f"SciPost Admin <admin@{domain}>",
                    [user.email],
                    connection=connection,
                    cc=addresses_cc,
                    bcc=addresses_bcc,
                )
                message.attach_alternative(html_version, "text/html")
                message.send()


class SendPrecookedEmailForm(forms.Form):
    email_address = forms.EmailField()
    email_option = forms.ModelChoiceField(
        queryset=PrecookedEmail.objects.filter(deprecated=False)
    )
    include_scipost_summary = forms.BooleanField(
        required=False, initial=False, label="Include SciPost summary at end of message"
    )
    from_address = forms.ChoiceField(choices=SCIPOST_FROM_ADDRESSES)


class ConfirmationForm(forms.Form):
    confirm = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=((True, "Confirm"), (False, "Abort")),
        label="",
    )


class SciPostPasswordResetForm(PasswordResetForm):
    def clean(self):
        super_clean = super().clean()

        users = User.objects.filter(email__iexact=self.cleaned_data.get("email"))
        if len(list(users)) == 0:
            self.add_error(
                "email",
                "There is no user associated with this email address.",
            )

        return super_clean

    def get_newly_registered_contributors(self, email: str):
        """
        Given an email, return a list of newly registered users with that email.
        """
        return Contributor.objects.filter(
            user__email__iexact=email, status=NEWLY_REGISTERED
        )

    def save(self, **kwargs):
        """
        Process users as PasswordResetForm does if they are active.
        If newly registered, Inactive users get a new activation link.
        """

        super().save(**kwargs)

        email = self.cleaned_data["email"]
        for contributor in self.get_newly_registered_contributors(email):
            contributor.generate_key()
            contributor.save()

            mail_util = DirectMailUtil(
                "contributors/new_activitation_link", contributor=contributor
            )
            mail_util.send_mail()

            self.has_sent_new_activation_link = True
