__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import random
import string
from typing import TYPE_CHECKING, Self
import uuid

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from anonymization.mixins import AnonymizableObjectMixin


from .behaviors import TimeStampedModel, orcid_validator
from .constants import (
    NORMAL_CONTRIBUTOR,
    DISABLED,
    TITLE_CHOICES,
    INVITATION_STYLE,
    INVITATION_TYPE,
    INVITATION_CONTRIBUTOR,
    INVITATION_FORMAL,
    AUTHORSHIP_CLAIM_PENDING,
    AUTHORSHIP_CLAIM_STATUS,
    CONTRIBUTOR_STATUSES,
    NEWLY_REGISTERED,
    TITLE_DR,
)
from .fields import ChoiceArrayField
from .managers import (
    ContributorManager,
    UnavailabilityPeriodManager,
    AuthorshipClaimQuerySet,
)

from conflicts.models import ConflictOfInterest

today = timezone.now().date()

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from django.contrib.auth.models import User
    from profiles.models import Profile
    from colleges.models.fellowship import Fellowship
    from submissions.models.assignment import EditorialAssignment


def get_sentinel_user():
    """Temporary fix to be able to delete Contributor instances.

    Eventually the 'to-be-removed-Contributor' should be status: "deactivated" and anonymized.
    Fallback user for models relying on Contributor that is being deleted.
    """
    user, __ = get_user_model().objects.get_or_create(username="deleted")
    return Contributor.objects.get_or_create(status=DISABLED, user=user)[0]


class TOTPDevice(models.Model):
    """
    Any device used by a User for 2-step authentication based on the RFC 6238 TOTP protocol.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    token = models.CharField(max_length=16)
    last_verified_counter = models.PositiveIntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        default_related_name = "devices"
        verbose_name = "TOTP Device"

    def __str__(self):
        return "{}: {}".format(self.user, self.name)


class Contributor(AnonymizableObjectMixin, models.Model):
    """Contributor is an extension of the User model.

    *Professionally active scientist* users of SciPost are Contributors.

    The username, password, email, first_name and last_name are inherited from User.

    Other information is carried by the related Profile.
    """

    profile = models.OneToOneField["Profile"](
        "profiles.Profile", on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.OneToOneField["User"](
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, unique=True
    )
    invitation_key = models.CharField(max_length=40, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=16, choices=CONTRIBUTOR_STATUSES, default=NEWLY_REGISTERED
    )
    address = models.CharField(max_length=1000, verbose_name="address", blank=True)
    vetted_by = models.ForeignKey["Contributor"](
        "self",
        on_delete=models.SET(get_sentinel_user),
        related_name="contrib_vetted_by",
        blank=True,
        null=True,
    )
    # If this Contributor is merged into another, then this field is set to point to the new one:
    duplicate_of = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
    )

    objects = ContributorManager()

    if TYPE_CHECKING:
        fellowships: "RelatedManager[Fellowship]"
        editorial_assignments: "RelatedManager[EditorialAssignment]"

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    @property
    def roles(self):
        r = []
        if self.user.is_superuser:
            r.append("su")
        if self.user.is_staff:
            r.append("st")
        return r if len(r) > 0 else None

    def __str__(self):
        val = "%s, %s" % (self.user.last_name, self.user.first_name)
        if self.user.is_superuser:
            val += " (su)"
        return val

    def save(self, *args, **kwargs):
        """Generate new activitation key if not set."""
        if not self.activation_key:
            self.generate_key()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return public information page url."""
        return reverse("scipost:contributor_info", args=(self.id,))

    @property
    def formal_str(self):
        return "%s %s" % (self.profile.get_title_display(), self.user.last_name)

    @property
    def is_active(self):
        """
        Checks if the Contributor is registered, vetted,
        and has not been deactivated for any reason.
        """
        # [TypeHint] Coerce to bool since `is_active` is a property of the `AbstractBaseUser` class.
        user_active: bool = self.user.is_active
        return user_active and self.status == NORMAL_CONTRIBUTOR

    @property
    def is_duplicate(self):
        return self.duplicate_of is not None

    @property
    def is_currently_available(self):
        """Check if Contributor is currently not marked as unavailable."""
        return not self.unavailability_periods.today().exists()

    @property
    def available_again_after_date(self):
        unav = self.unavailability_periods.today().first()
        if unav:
            return unav.end

    @property
    def is_scipost_admin(self):
        """Check if Contributor is a SciPost Administrator."""
        return (
            self.user.groups.filter(name="SciPost Administrators").exists()
            or self.user.is_superuser
        )

    @property
    def is_ed_admin(self):
        """Check if Contributor is an Editorial Administrator."""
        return (
            self.user.groups.filter(name="Editorial Administrators").exists()
            or self.user.is_superuser
        )

    @property
    def is_in_advisory_board(self):
        """Check if Contributor is in the Advisory Board."""
        return (
            self.user.groups.filter(name="Advisory Board").exists()
            or self.user.is_superuser
        )

    @property
    def is_active_fellow(self):
        """Check if Contributor is a member of the Editorial College."""
        return self.fellowships.active().exists() or self.user.is_superuser

    @property
    def is_active_senior_fellow(self):
        return self.fellowships.active().senior().exists() or self.user.is_superuser

    def session_fellowship(self, request):
        """Return session's fellowship, if any; if Fellow, set session_fellowship_id if not set."""
        fellowships = self.fellowships.active()
        if fellowships.exists():
            if request.session["session_fellowship_id"]:
                from colleges.models import Fellowship

                try:
                    return self.fellowships.active().get(
                        pk=request.session["session_fellowship_id"]
                    )
                except Fellowship.DoesNotExist:
                    return None
            # set the session's fellowship_id to default
            fellowship = fellowships.first()
            request.session["session_fellowship_id"] = fellowship.id
            return fellowship
        return None

    @property
    def is_vetting_editor(self):
        """Check if Contributor is a Vetting Editor."""
        return (
            self.user.groups.filter(name="Vetting Editors").exists()
            or self.user.is_superuser
        )

    @property
    def profile_title(self) -> str:
        return self.profile.get_title_display() if self.profile else TITLE_DR

    def generate_key(self, feed=""):
        """Generate a new activation_key for the contributor, given a certain feed."""
        for i in range(5):
            feed += random.choice(string.ascii_letters)
        feed = feed.encode("utf8")
        salt = self.user.username.encode("utf8")
        self.activation_key = hashlib.sha1(salt + feed).hexdigest()
        self.key_expires = timezone.now() + datetime.timedelta(days=2)

    def conflict_of_interests(self):
        if not self.profile:
            return ConflictOfInterest.objects.none()
        return ConflictOfInterest.objects.filter_for_profile(self.profile)

    @classmethod
    def create_anonymous(cls, uuid_str: str | None = None) -> "Self":
        """Create an anonymous contributor with optional UUID last name."""
        from profiles.models import Profile

        uuid_str = str(uuid.uuid4()) if uuid_str is None else uuid_str

        anonymous_profile = Profile.create_anonymous(uuid_str)
        return cls.objects.create(
            is_anonymous=True,
            status=DISABLED,
            user=anonymous_user,
            profile=anonymous_profile,
        )


class UnavailabilityPeriod(models.Model):
    contributor = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="unavailability_periods",
    )
    start = models.DateField()
    end = models.DateField()

    objects = UnavailabilityPeriodManager()

    class Meta:
        ordering = ["-start"]

    def __str__(self):
        return "%s (%s to %s)" % (self.contributor, self.start, self.end)


class Remark(models.Model):
    """A form of non-public communication for VGMs and/or submissions and recommendations."""

    contributor = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, blank=True, null=True
    )
    recommendation = models.ForeignKey(
        "submissions.EICRecommendation", on_delete=models.CASCADE, blank=True, null=True
    )
    date = models.DateTimeField(auto_now_add=True)
    remark = models.TextField()

    class Meta:
        default_related_name = "remarks"
        ordering = ["date"]

    def __str__(self):
        return (
            self.contributor.user.first_name
            + " "
            + self.contributor.user.last_name
            + " on "
            + self.date.strftime("%Y-%m-%d")
        )


###############
# Invitations #
###############


class RegistrationInvitation(models.Model):
    """Deprecated: Use the `invitations` app"""

    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField()
    invitation_type = models.CharField(
        max_length=2, choices=INVITATION_TYPE, default=INVITATION_CONTRIBUTOR
    )
    cited_in_submission = models.ForeignKey(
        "submissions.Submission",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="registration_invitations",
    )
    cited_in_publication = models.ForeignKey(
        "journals.Publication", on_delete=models.CASCADE, blank=True, null=True
    )
    message_style = models.CharField(
        max_length=1, choices=INVITATION_STYLE, default=INVITATION_FORMAL
    )
    personal_message = models.TextField(blank=True)
    invitation_key = models.CharField(max_length=40, unique=True)
    key_expires = models.DateTimeField(default=timezone.now)
    date_sent = models.DateTimeField(default=timezone.now)
    invited_by = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE, blank=True, null=True
    )
    nr_reminders = models.PositiveSmallIntegerField(default=0)
    date_last_reminded = models.DateTimeField(blank=True, null=True)
    responded = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    def __str__(self):
        return "DEPRECATED"


class CitationNotification(models.Model):
    """Deprecated: Use the `invitations` app"""

    contributor = models.ForeignKey("scipost.Contributor", on_delete=models.CASCADE)
    cited_in_submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, blank=True, null=True
    )
    cited_in_publication = models.ForeignKey(
        "journals.Publication", on_delete=models.CASCADE, blank=True, null=True
    )
    processed = models.BooleanField(default=False)


class AuthorshipClaim(models.Model):
    claimant = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE, related_name="claimant"
    )
    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, blank=True, null=True
    )
    commentary = models.ForeignKey(
        "commentaries.Commentary", on_delete=models.CASCADE, blank=True, null=True
    )
    thesislink = models.ForeignKey(
        "theses.ThesisLink", on_delete=models.CASCADE, blank=True, null=True
    )
    vetted_by = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE, blank=True, null=True
    )
    status = models.SmallIntegerField(
        choices=AUTHORSHIP_CLAIM_STATUS, default=AUTHORSHIP_CLAIM_PENDING
    )

    objects = AuthorshipClaimQuerySet.as_manager()

    def __str__(self):
        if self.submission:
            return "Authorship claim: %s for %s %s" % (
                self.claimant,
                "Submission",
                self.submission,
            )
        elif self.commentary:
            return "Authorship claim: %s for %s %s" % (
                self.claimant,
                "Commentary",
                self.commentary,
            )
        elif self.thesislink:
            return "Authorship claim: %s for %s %s" % (
                self.claimant,
                "Thesis Link",
                self.thesislink,
            )
        return "Authorship claim: %s for [undefined]" % self.claimant


class PrecookedEmail(models.Model):
    """
    Each instance contains an email template in both plain and html formats.
    Can only be created by Admins.
    For further use in scipost:send_precooked_email method.
    """

    email_subject = models.CharField(max_length=300)
    email_text = models.TextField()
    email_text_html = models.TextField()
    date_created = models.DateField(default=timezone.now)
    emailed_to = ArrayField(models.EmailField(blank=True), blank=True)
    date_last_used = models.DateField(default=timezone.now)
    deprecated = models.BooleanField(default=False)

    def __str__(self):
        return self.email_subject
