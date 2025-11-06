__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from email.utils import make_msgid
import bleach
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.validators import RegexValidator
from django.db.models import Q, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils.encoding import force_bytes
from django.utils.html import format_html
from django.utils.http import urlsafe_base64_encode
import pyotp
import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.utils.dates import MONTHS

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, ButtonHolder, Submit
from crispy_bootstrap5.bootstrap5 import FloatingField
from dal import autocomplete

from common.utils.text import split_strip
from invitations.constants import STATUS_REGISTERED
from mails.models import MailAddressDomain
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
from invitations.models import CitationNotification, RegistrationInvitation
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

    The form may get an optional "profile" kwarg, which will be used
    to pre-fill the form with the data of the Profile to be registered.
    Then, all fields will be propagated to the Profile, and a Contributor
    will be created for it. An "invitation_key" may be pre-filled as initial
    and can be used to match the passed Profile to a RegistrationInvitation,
    which will be used to set the Contributor's field.
    """

    required_css_class = "required-asterisk"

    invitation_key = forms.CharField(
        max_length=40, widget=forms.HiddenInput(), required=False
    )
    institutional_email = forms.EmailField(
        label="Institutional Email address",
        help_text="An academic email address, used to verify your credentials "
        "and act as a primary communications channel. "
        "It also can be used in place of your username for login.",
    )
    personal_email = forms.EmailField(
        label="Personal (Recovery) Email address",
        help_text="A personal email address to recover your account "
        "in case you lose access to your institutional email address.",
    )
    title = forms.ChoiceField(choices=TITLE_CHOICES, label="Title")
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

    def __init__(
        self,
        *args,
        profile: Profile | None = None,
        **kwargs,
    ):
        if profile:
            form_initials = {
                "title": profile.title,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "first_name_original": profile.first_name_original,
                "last_name_original": profile.last_name_original,
                "orcid_id": profile.orcid_id,
                "webpage": profile.webpage,
                "institutional_email": profile.email,
                "acad_field": profile.acad_field,
                "specialties": profile.specialties.all(),
            } | kwargs.pop("initial", {})
            super().__init__(*args, initial=form_initials, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def clean(self):
        """
        Check that:
        * either an organization or an address are provided
        * the emails provided do not belong to another profile
        * the ORCID ID provided does not belong to another profile
        """
        cleaned_data = super(RegistrationForm, self).clean()
        current_affiliation = cleaned_data.get("current_affiliation", None)
        address = cleaned_data.get("address", "")

        if current_affiliation is None and address == "":
            raise forms.ValidationError(
                "You must either specify a Current Affiliation, or "
                "fill in the institution name and address field"
            )

        # Check email existing in other profiles
        invitation_key = self.cleaned_data.get("invitation_key", "")
        self._forbid_already_associated_email("institutional_email", invitation_key)
        self._forbid_already_associated_email("personal_email", invitation_key)

        # Check institutional email is not of a "personal" domain, unless invited
        institutional_email = self.cleaned_data.get("institutional_email", "")
        institutional_address_domain_is_personal = MailAddressDomain.objects.filter(
            domain__iexact=institutional_email.split("@")[-1],
            kind=MailAddressDomain.KIND_PERSONAL,
        ).exists()
        if not invitation_key and institutional_address_domain_is_personal:
            self.add_error(
                "institutional_email",
                "Please do not use a personal address for academic credential verification purposes.",
            )

        # If ORCID exists in another profile
        duplicate_orcid_profile = Profile.objects.filter(
            orcid_id=cleaned_data.get("orcid_id", "")
        ).first()
        invitation = RegistrationInvitation.objects.filter(
            invitation_key=cleaned_data.get("invitation_key", "")
        ).first()
        invitation_profile = invitation.profile if invitation else None
        if duplicate_orcid_profile and invitation_profile != duplicate_orcid_profile:
            error_message = format_html(
                "This ORCID id is already in use. Have you already registered?"
                "<a href='/password_reset/'>Reset your password</a> or "
                "<a href='mailto:techsupport@scipost.org'>contact tech support</a>."
            )
            self.add_error("orcid_id", error_message)

    def clean_invitation_key(self):
        """
        Validates that the invitation key matches a non-deprecated RegistrationInvitation,
        """
        INSTRUCTIONS = (
            "Please click the link in the invitation email to register, or "
            "contact techsupport@scipost.org if the issue persists."
        )

        if not (key := self.cleaned_data.get("invitation_key", "")):
            return ""

        invitation = RegistrationInvitation.objects.filter(invitation_key=key).first()

        if not invitation:
            return self.add_error(
                None,
                "The invitation key you provided is invalid. " + INSTRUCTIONS,
            )

        already_registered = (
            Contributor.objects.filter(invitation_key=key).first() is not None
        )

        if invitation.profile is None:
            return self.add_error(
                None, "No profile associated to given invitation key. " + INSTRUCTIONS
            )
        elif invitation.has_responded or already_registered:
            return self.add_error(
                None,
                "This invitation token has already been used to register an account. "
                + INSTRUCTIONS,
            )
        elif timezone.now() > invitation.key_expires:
            return self.add_error(
                None, "The invitation key has expired. " + INSTRUCTIONS
            )

        return invitation.invitation_key

    def _forbid_already_associated_email(self, field: str, key: str = ""):
        """
        Check that the email field does not correspond to an existing ProfileEmail,
        unless it is the one the user is registering for.
        If so, reply with an appropriate error message for the following cases:
        - Already registered account with this email address
        - Pending registration invitation with this email address
        - Pending registration invitation with a synonymous name
        - Generic error message otherwise
        """
        # fmt: off
        profile_trying_to_register_for = (
            ref.referee
            if (ref := RefereeInvitation.objects.filter(invitation_key=key).first())
            else reg.profile
            if (reg := RegistrationInvitation.objects.filter(invitation_key=key).first())
            else None
        )
        # fmt: on

        field_address = self.cleaned_data.get(field, "")
        profile_email = (
            ProfileEmail.objects.filter(email__iexact=field_address)
            .exclude(profile=profile_trying_to_register_for)
            .first()
        )
        if profile_email is None:
            return  # No account associated with this email, no errors here

        three_months_ago = timezone.now() - datetime.timedelta(days=90)
        pending_reg_invitations = RegistrationInvitation.objects.sent().filter(
            created__gt=three_months_ago
        )
        pending_ref_invitations = RefereeInvitation.objects.awaiting_response().filter(
            date_invited__gt=three_months_ago
        )
        has_been_invited = (
            pending_reg_invitations.filter(
                Q(profile=profile_email.profile) | Q(email=field_address)
            ).exists()
            or pending_ref_invitations.filter(
                Q(referee=profile_email.profile) | Q(email_address=field_address)
            ).exists()
        )
        has_synonymous_been_invited = (
            pending_reg_invitations.filter(
                profile__full_name_normalized=profile_email.profile.full_name_normalized
            )
            .exclude(profile=profile_email.profile)
            .exists()
        ) or (
            pending_ref_invitations.filter(
                referee__full_name_normalized=profile_email.profile.full_name_normalized
            )
            .exclude(referee=profile_email.profile)
            .exists()
        )
        has_registered = Contributor.objects.filter(
            profile=profile_email.profile
        ).exists()

        if has_registered:
            error_message = (
                "There exists another account with this email address. <br />"
                "Please <a href='/password_reset/'>reset your password</a> if it belongs to you or "
                "<a href='mailto:techsupport@scipost.org'>contact tech support</a> if you need assistance."
            )
        elif has_been_invited:
            error_message = (
                "You have been invited to register an account with this email address. <br />"
                "Please click the link in the invitation email you received to register. <br />"
                "<a href='mailto:techsupport@scipost.org'>Contact tech support</a> if unable to do so."
            )
        elif has_synonymous_been_invited:
            error_message = (
                "This email address is associated to a profile for which another similarly-named profile is pending registration. <br />"
                "If it belongs to you, please check your alternate emails accounts where a possible invitation may have been sent. <br />"
                "<a href='mailto:techsupport@scipost.org'>Contact tech support</a> if you need assistance with this."
            )
        else:
            #! FIXME: In the future it would be nice to send a kind of verification email
            # that turns into a registration invitation upon completion. This would automate
            # the process of claiming a profile with a reasonable test.
            error_message = (
                "A profile with this email address exists but is not associated to a registered account. <br />"
                "Please <a href='mailto:techsupport@scipost.org'>contact tech support</a> verify it is yours and claim it."
            )

        self.add_error(field, format_html(error_message))

    def clean_personal_email(self):
        personal_email = self.cleaned_data.get("personal_email", "")
        mail_domain = personal_email.split("@")[-1]
        if MailAddressDomain.objects.filter(
            domain__iexact=mail_domain, kind=MailAddressDomain.KIND_INSTITUTIONAL
        ).exists():
            self.add_error(
                "personal_email",
                "Please do not use an institutional address for recovery purposes.",
            )

        return personal_email

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        user = User(
            username=self.cleaned_data.get("username", ""),
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
            email=self.cleaned_data.get("institutional_email", ""),
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

    def create_and_save_contributor(self):
        user = User.objects.create_user(
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["institutional_email"],
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            is_active=False,  # Initially inactive until vetted
        )

        # Structure form data into a Profile object
        profile_data = {
            "title": self.cleaned_data["title"],
            "first_name": self.cleaned_data["first_name"],
            "last_name": self.cleaned_data["last_name"],
            "first_name_original": self.cleaned_data["first_name_original"],
            "last_name_original": self.cleaned_data["last_name_original"],
            "acad_field": self.cleaned_data["acad_field"],
            "orcid_id": self.cleaned_data["orcid_id"] or None,
            "webpage": self.cleaned_data["webpage"],
        }

        key = self.cleaned_data.get("invitation_key", "")
        invitation = RegistrationInvitation.objects.filter(invitation_key=key).first()

        if invitation:
            invitation.status = STATUS_REGISTERED
            invitation.save()

        # If an invitation key is provided, use its profile, otherwise create a new one
        profile = invitation.profile if invitation else None
        if profile is not None:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        else:
            profile = Profile.objects.create(**profile_data)

        profile.specialties.set(self.cleaned_data["specialties"])

        institutional_email, created = ProfileEmail.objects.get_or_create(
            email=self.cleaned_data["institutional_email"],
            profile=profile,
            defaults={"primary": True},
        )
        institutional_email.set_primary()

        personal_email, created = ProfileEmail.objects.get_or_create(
            email=self.cleaned_data["personal_email"],
            profile=profile,
            defaults={"primary": False, "kind": ProfileEmail.KIND_RECOVERY},
        )
        if not created:
            personal_email.primary = False
            personal_email.kind = ProfileEmail.KIND_RECOVERY
            personal_email.save()

        # Create an Affiliation for this Profile
        current_affiliation = self.cleaned_data.get("current_affiliation", None)
        if current_affiliation:
            Affiliation.objects.create(
                profile=profile, organization=current_affiliation
            )
        # Create the Contributor object
        contributor, __ = Contributor.objects.get_or_create(
            profile=profile,
            dbuser=user,
            defaults=dict(
                invitation_key=key,
                address=self.cleaned_data["address"],
            ),
        )
        contributor.save()

        # Automatically vet the Contributor if they have an invitation key
        # or if their institutional email is from a known domain.
        if contributor.invitation_key or institutional_email.has_institutional_domain:
            contributor.status = NORMAL_CONTRIBUTOR
            contributor.save()
            group = Group.objects.get(name="Registered Contributors")
            contributor.dbuser.groups.add(group)
            contributor.dbuser.save()

        return contributor


class ModifyPersonalMessageForm(forms.Form):
    personal_message = forms.CharField(widget=forms.Textarea())


class UpdateUserDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["last_name"].widget.attrs["disabled"] = True

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
        widget=forms.Textarea({"rows": 4}), label="Justification", required=False
    )

    def __init__(self, *args, **kwargs):
        self.contributor_id = kwargs.pop("contributor_id")

        if args and len(args) > 0 and (data := args[0]):
            # Create an editable dict from the QueryDict keeping only Truthy values
            # This is to avoid empty fields in the form counting as "bound".
            data = {k: v for k, v in data.items() if v}
            if data.get("refusal_reason") == UNVERIFIABLE_CREDENTIALS:
                data.setdefault(
                    "email_response_field",
                    "Unfortunately, we were unable to verify your affiliation to a research organization. "
                    "Please register again using an email address issued by your organization.",
                )

        super().__init__(data, *args[1:], **kwargs)
        self.auto_id = "%s_" + str(self.contributor_id)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("decision", css_class="d-flex flex-row flex-wrap gap-3"),
        )

        if self.data.get("decision") == "False":
            self.fields["refusal_reason"].required = True
            self.helper.layout.extend(
                (Field("refusal_reason"), Field("email_response_field"))
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

    next = forms.CharField(required=False)
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "current-password"}, render_value=True
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(FloatingField("username"), css_class="col-12"),
                Div(FloatingField("password"), css_class="col-12"),
                Div(FloatingField("next"), css_class="d-none"),
                Div(
                    Submit("submit", "Login", css_class="btn btn-primary"),
                    css_class="col-12",
                ),
                css_class="row",
            )
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
        if user.contributor.status not in (NEWLY_REGISTERED, NORMAL_CONTRIBUTOR):
            raise forms.ValidationError(
                (
                    "Your registration request has been turned down. "
                    "You are still able to view all SciPost content, "
                    "but not log in or contribute new one."
                ),
                code="rejected",
            )
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


class SciPostMFAVerifyForm(SciPostAuthenticationForm):
    code = forms.CharField(
        label="2FA Code",
        max_length=6,
        required=True,
        validators=[RegexValidator(r"^\d{6}$", "Enter a valid 6-digit code.")],
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "placeholder": "000000",
                "autofocus": "autofocus",
                "pattern": r"\d{6}",
                "inputmode": "numeric",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field("code"), css_class="col-12"),
                Div(Field("username"), css_class="d-none"),
                Div(Field("password"), css_class="d-none"),
                Div(Field("next"), css_class="d-none"),
                Div(
                    Submit("submit", "Login", css_class="btn btn-primary"),
                    css_class="col-12",
                ),
                css_class="row",
            )
        )

    def clean(self):
        super_clean = super().clean()

        if code := super_clean.get("code", ""):
            code_verified = TOTPVerification(self.get_user()).verify_code(code)
            if not code_verified:
                self.add_error(
                    "code",
                    "The code you entered is invalid. Please try again.",
                )

        return super_clean


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
        fields = ["token", "name"]
        labels = {"name": "Device name", "token": "Secret Key"}

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user")
        super().__init__(*args, **kwargs)
        self.initial["token"] = pyotp.random_base32()
        self.fields["token"].widget.attrs.update(
            {"autocomplete": "off", "readonly": True}
        )
        self.fields["token"].help_text = (
            "This is the secret key for your device. "
            "You can scan the QR code or copy it to your authenticator app."
        )
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
            self.current_user.username, issuer_name="SciPost"
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        code = cleaned_data.get("code")
        if not TOTPVerification.verify_token(self.secret_key, code):
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
                    headers={"Message-ID": make_msgid(domain=domain)},
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
    def clean_email(self):
        email = self.cleaned_data["email"]

        matching_users = list(self.get_users(email))

        if not matching_users:
            self.add_error(
                "email",
                "There is no active account associated with this email address.",
            )

        for user in matching_users:
            if not user.recovery_email_matches:
                password_reset_domain = user.password_reset_email.split("@")[-1]
                censored_recovery_email = (
                    user.password_reset_email[0] + "*****@" + password_reset_domain
                )
                self.add_error(
                    "email",
                    "The email address you have entered is not set as your recovery email. "
                    f"Please enter your full recovery email address ({censored_recovery_email}) to reset your password.",
                )

        return email

    def get_newly_registered_contributors(self, email: str):
        """
        Given an email, return a list of newly registered users with that email.
        """
        return Contributor.objects.filter(
            dbuser__email__iexact=email, status=NEWLY_REGISTERED
        )

    def get_users(self, email: str):
        """
        Return users associated with the given email address,
        who are also active and have a usable password.
        """
        matched_active_users = (
            User.objects.annotate(
                recovery_email=Subquery(
                    ProfileEmail.objects.filter(
                        profile__contributor__dbuser=OuterRef("pk"),
                        kind=ProfileEmail.KIND_RECOVERY,
                    ).values("email")[:1]
                ),
                primary_email=Subquery(
                    ProfileEmail.objects.filter(
                        profile__contributor__dbuser=OuterRef("pk"),
                        primary=True,
                    ).values("email")[:1]
                ),
                # Default to primary or login email if no recovery email is set
                password_reset_email=Coalesce(
                    "recovery_email",
                    "primary_email",
                    "email",
                ),
                # Determine which address was entered
                recovery_email_matches=Q(recovery_email__iexact=email),
                primary_email_matches=Q(primary_email__iexact=email),
                login_email_matches=Q(email__iexact=email),
                password_reset_email_matches=Q(password_reset_email__iexact=email),
                other_email_matches=Q(
                    contributor__profile__emails__email__iexact=email
                ),
            )
            # Must either match the login email (on User) or any ProfileEmail
            .filter(Q(login_email_matches=True) | Q(other_email_matches=True))
            .filter(is_active=True)
            .order_by("id")
            .distinct("id")
        )

        return (u for u in matched_active_users if u.has_usable_password())

    def save(
        self,
        domain_override=None,
        use_https=False,
        token_generator=default_token_generator,
        request=None,
        **kwargs,
    ):
        """
        Process users as PasswordResetForm does if they are active.
        If newly registered, Inactive users get a new activation link.
        """
        email = self.cleaned_data["email"]

        # Copy of Django's default implementation
        # because I'm not allowed to override the "to" address.
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override

        for user in self.get_users(email):
            user_email = user.password_reset_email
            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
            }
            self.send_mail(
                kwargs.get("subject_template_name"),
                kwargs.get("email_template_name"),
                context,
                kwargs.get("from_email"),
                user_email,
                html_email_template_name=kwargs.get("html_email_template_name"),
            )

        for contributor in self.get_newly_registered_contributors(email):
            contributor.generate_key()
            contributor.save()

            mail_util = DirectMailUtil(
                "contributors/new_activitation_link", contributor=contributor
            )
            mail_util.send_mail()

            self.has_sent_new_activation_link = True
