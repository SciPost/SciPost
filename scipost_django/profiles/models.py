__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import secrets
from typing import TYPE_CHECKING, Iterable
import uuid
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Q, Exists, OuterRef

from django.urls import reverse
from django.db import models
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils import timezone

from anonymization.mixins import AnonymizableObjectMixin
from mails.utils import DirectMailUtil
from organizations.utils import RORAPIHandler
from scipost.behaviors import orcid_validator
from scipost.constants import TITLE_CHOICES, TITLE_DR
from scipost.models import Contributor

from comments.models import Comment
from journals.models import Publication, PublicationAuthorsTable
from ontology.models import Topic
from theses.models import ThesisLink

from .constants import (
    PROFILE_NON_DUPLICATE_REASONS,
    AFFILIATION_CATEGORIES,
    AFFILIATION_CATEGORY_UNSPECIFIED,
)
from .managers import (
    ProfileEmailQuerySet,
    ProfileManager,
    ProfileQuerySet,
    AffiliationQuerySet,
)

from mails.models import MailAddressDomain

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from submissions.models.referee_invitation import RefereeInvitation


class Profile(AnonymizableObjectMixin, models.Model):
    """
    A Profile object instance contains information about an individual.

    This individual is a potential SciPost Contributor but is not necessarily registered.
    It is created and used by Admin, EdAdmin or other internal SciPost staff.

    For registered Contributors, a profile is initially created from the contributor-filled
    information in the Contributor object. Profile should thus be viewed as containing
    the Admin-certified version of this information.

    The information is only partial, and is meant to be used among others to:

    * help with editorial matters:

       * help EdAdmin identify prospective Fellows
       * help Fellows identify appropriate referees
       * mark potential conflicts of interest

    * allow respecting people's preferences:

       * mark somebody as not willing to receive emails from SciPost.
       * mark somebody as a non-referee (if that person does not want to referee for SciPost)
    """

    if TYPE_CHECKING:
        from submissions.models.submission import SubmissionAuthorProfile
        from invitations.models import RegistrationInvitation
        from colleges.models import FellowshipNomination, PotentialFellowship
        from anonymization.models import ProfileAnonymization

        id: int
        contributor: Contributor | None
        referee_invitations: "RelatedManager[RefereeInvitation]"
        emails: "RelatedManager[ProfileEmail]"
        affiliations: "RelatedManager[Affiliation]"
        submissionauthorprofile_set: "RelatedManager[SubmissionAuthorProfile]"
        publicationauthorstable_set: "RelatedManager[PublicationAuthorsTable]"
        registrationinvitation_set: "RelatedManager[RegistrationInvitation]"
        potentialfellowship_set: "RelatedManager[PotentialFellowship]"
        fellowship_nominations: "RelatedManager[FellowshipNomination]"
        eponymization: "ProfileAnonymization | None"

    title = models.CharField(max_length=4, choices=TITLE_CHOICES, default=TITLE_DR)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    first_name_original = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="First name (original)",
        help_text="Optional: Name in non-Latin alphabet",
    )
    last_name_original = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Last name (original)",
        help_text="Optional: Name in non-Latin alphabet",
    )

    orcid_authenticated = models.BooleanField(default=False)
    orcid_id = models.CharField(
        max_length=20,
        verbose_name="ORCID id",
        blank=True,
        null=True,
        validators=[orcid_validator],
    )

    webpage = models.URLField(max_length=300, blank=True)

    # Ontology-based semantic linking
    acad_field = models.ForeignKey(
        "ontology.AcademicField",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="profiles",
    )
    specialties = models.ManyToManyField(
        "ontology.Specialty", blank=True, related_name="profiles"
    )
    topics = models.ManyToManyField("ontology.Topic", blank=True)

    # Preferences for interactions with SciPost:
    accepts_SciPost_emails = models.BooleanField(default=True)
    accepts_refereeing_requests = models.BooleanField(default=True)

    red_flags = GenericRelation(
        "ethics.RedFlag",
        object_id_field="concerning_object_id",
        content_type_field="concerning_object_type",
        related_query_name="profile",
    )

    objects = ProfileManager()

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["orcid_id"],
                name="unique_orcid_id",
                condition=Q(orcid_id__isnull=False),
                violation_error_message="ORCID id must be unique across all profiles.",
            ),
            models.CheckConstraint(
                check=Q(orcid_id__isnull=True)
                | Q(orcid_id__regex=r"^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$"),
                name="orcid_id_format",
                violation_error_message="ORCID id must be of the form 'XXXX-XXXX-XXXX-XXXY', "
                "where X is a digit and Y is a digit or 'X'.",
            ),
        ]

    def __str__(self):
        return "%s, %s %s" % (
            self.last_name,
            self.get_title_display() if self.title != None else "",
            self.first_name,
        )

    @property
    def full_name(self):
        """The full name: first name + last name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def formal_name(self):
        """The formal name: title + last name."""
        return f"{self.get_title_display()} {self.last_name}"

    @property
    def full_name_original(self):
        """The full name in original script: first name + last name."""
        return f"{self.first_name_original} {self.last_name_original}"

    @property
    def roles(self):
        try:
            return self.contributor.roles
        except (KeyError, Contributor.DoesNotExist):
            return None

    def str_with_roles(self):
        r = self.roles
        return "%s, %s %s%s" % (
            self.last_name,
            self.get_title_display() if self.title != None else "",
            self.first_name,
            f" ({','.join(r)})" if r else "",
        )

    @property
    def email(self):
        return getattr(self.emails.filter(primary=True).first(), "email", "")

    @property
    def has_active_contributor(self):
        try:
            return self.contributor is not None and self.contributor.is_active
        except Contributor.DoesNotExist:
            return False

    def get_absolute_url(self):
        return reverse("profiles:profile_detail", kwargs={"pk": self.id})

    def additional_publication_affiliations(self):
        """
        Returns additional PublicationAuthorsTable affiliations
        excluding the ones from the Profile's own affiliations.
        """
        return (
            self.publicationauthorstable_set.annotate(
                has_declared_affiliation=Exists(
                    self.affiliations.filter(
                        organization__in=OuterRef("affiliations__id")
                    )
                )
            )
            .exclude(has_declared_affiliation=True)
            .order_by("id", "-publication__publication_date")
            .prefetch_related("affiliations")
            .distinct("id")
        )

    def publications(self):
        """
        Returns all the publications associated to this Profile.
        """
        return Publication.objects.published().filter(authors__profile=self)

    def comments(self):
        """
        Returns all the Comments associated to this Profile.
        """
        return Comment.objects.filter(author__profile=self)

    def theses(self):
        """
        Returns all the Theses associated to this Profile.
        """
        return ThesisLink.objects.filter(author_as_cont__profile=self)

    def has_competing_interest_with(self, profile):
        """
        Returns True if this Profile has a CompetingInterest with the given Profile.
        """
        from ethics.models import CompetingInterest

        return CompetingInterest.objects.filter(
            Q(profile=self, related_profile=profile)
            | Q(related_profile=self, profile=profile)
        ).exists()

    @classmethod
    def create_anonymous(cls, uuid_str: str | None = None):
        """Create an anonymous profile."""
        return cls.objects.create(
            is_anonymous=True,
            title="MX",
            first_name="Anonymous",
            last_name=uuid_str or str(uuid.uuid4()),
            accepts_SciPost_emails=False,
            accepts_refereeing_requests=False,
        )


class ProfileEmail(models.Model):
    """Any email related to a Profile instance."""

    KIND_COMMUNICATION = "communication"
    KIND_RECOVERY = "recovery"

    profile = models.ForeignKey[Profile]("profiles.Profile", on_delete=models.CASCADE)
    email = models.EmailField()
    domain = models.ForeignKey["MailAddressDomain"](
        "mails.MailAddressDomain",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="profile_emails",
    )
    kind = models.CharField(
        max_length=32,
        choices=[
            (KIND_COMMUNICATION, "Communication"),
            (KIND_RECOVERY, "Recovery"),
        ],
        default=KIND_COMMUNICATION,
    )
    still_valid = models.BooleanField(default=True)
    primary = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=128, null=True)
    token_expiration = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="profile_emails_added",
    )

    objects = ProfileEmailQuerySet.as_manager()

    if TYPE_CHECKING:
        objects: models.Manager["ProfileEmail"]

    class Meta:
        unique_together = ["profile", "email"]
        ordering = ["-primary", "-still_valid", "email"]
        default_related_name = "emails"

    def __str__(self):
        return self.email

    def reset_verification_token(self):
        self.verified = False
        self.verification_token = secrets.token_urlsafe(40)
        self.token_expiration = timezone.now() + datetime.timedelta(hours=48)
        self.save()

    @property
    def has_token_expired(self):
        return timezone.now() > self.token_expiration

    @property
    def has_institutional_domain(self):
        return (
            self.domain is not None
            and self.domain.kind == MailAddressDomain.KIND_INSTITUTIONAL
        )

    @property
    def has_personal_domain(self):
        return (
            self.domain is not None
            and self.domain.kind == MailAddressDomain.KIND_PERSONAL
        )

    def _find_domain(self):
        """
        Return the MailAddressDomain matching this email's domain or None if not found.
        """
        domain_name = self.email.split("@")[-1].strip().lower()

        domain, created = MailAddressDomain.objects.get_or_create(domain=domain_name)
        if created:
            # Attempt to fetch from the ROR API if the domain was just created
            try:
                if found_ROR_ids := RORAPIHandler.query_for_domain(domain_name):
                    domain.ror_id_matches = found_ROR_ids
                    domain.kind = MailAddressDomain.KIND_INSTITUTIONAL
                    domain.save()
            except Exception:
                # Whatever the error, there's no reason to fail here
                pass

        return domain

    def save(self, *args, **kwargs):
        """
        Override to update the MailAddressDomain on save.
        """
        self.domain = self._find_domain()

        super().save(*args, **kwargs)

    def send_verification_email(self):
        if self.has_token_expired:
            self.reset_verification_token()

        mail_sender = DirectMailUtil("profiles/verify_profile_email", object=self)
        mail_sender.send_mail()

    def get_verification_url(self):
        return reverse(
            "profiles:verify_profile_email",
            kwargs={"email_id": self.id, "token": self.verification_token},
        )

    def set_primary(self):
        """
        Sets this email as the primary email for the Profile, unsetting others.
        """
        self.profile.emails.update(primary=False)
        self.primary = True
        self.save()

        # Propagate the change to User if it exists
        try:
            if user := self.profile.contributor.user:
                user.email = self.email
                user.save()
        except (Contributor.DoesNotExist, AttributeError):
            # If the profile does not have a contributor or user, we do nothing
            pass

    def set_recovery(self):
        """
        Sets this email as the recovery email for the Profile, unsetting others.
        """
        self.profile.emails.update(kind=ProfileEmail.KIND_COMMUNICATION)
        self.kind = ProfileEmail.KIND_RECOVERY
        self.save()


def get_profiles(slug):
    """
    Returns a list of Profiles for which there exists at least one
    Publication/Submission object carrying this Topic.
    """
    topic = get_object_or_404(Topic, slug=slug)
    publications = PublicationAuthorsTable.objects.filter(
        publication__topics__in=[
            topic,
        ]
    )
    profile_id_list = [tbl.profile.id for tbl in publications.all()]
    return Profile.objects.filter(id__in=profile_id_list).distinct()


class ProfileNonDuplicates(models.Model):
    """
    Sets of Profiles which are not duplicates of each other,
    and thus can be filtered out of any dynamically generated list of potential duplicates.
    """

    profiles = models.ManyToManyField("profiles.Profile")
    reason = models.CharField(max_length=32, choices=PROFILE_NON_DUPLICATE_REASONS)

    class Meta:
        verbose_name = "Profile non-duplicates"
        verbose_name_plural = "Profile non-duplicates"

    def __str__(self):
        return "%s, %s (%i)" % (
            self.profiles.first().last_name,
            self.profiles.first().first_name,
            self.profiles.count(),
        )

    @property
    def full_name(self):
        return "%s%s" % (
            self.profiles.first().last_name,
            self.profiles.first().first_name,
        )


################
# Affiliations #
################


class Affiliation(models.Model):
    """
    Link between a Profile and an Organization, for a specified time interval.

    Fields:

    * profile
    * organization
    * category
    * description
    * date_from
    * date_until

    Affiliations can overlap in time.

    Ideally, each Profile would have at least one valid Affiliation at each moment
    of time during the whole duration of that person's career.
    """

    profile = models.ForeignKey(
        "profiles.Profile", on_delete=models.CASCADE, related_name="affiliations"
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="affiliations",
    )
    category = models.CharField(
        max_length=64,
        choices=AFFILIATION_CATEGORIES,
        default=AFFILIATION_CATEGORY_UNSPECIFIED,
        help_text="Select the most suitable category",
    )
    description = models.CharField(max_length=256, blank=True, null=True)
    date_from = models.DateField(blank=True, null=True)
    date_until = models.DateField(blank=True, null=True)

    objects = AffiliationQuerySet.as_manager()

    class Meta:
        default_related_name = "affiliations"
        ordering = ["profile__last_name", "profile__first_name", "-date_until"]

    def __str__(self):
        return "%s, %s [%s to %s]" % (
            str(self.profile),
            str(self.organization),
            self.date_from.strftime("%Y-%m-%d") if self.date_from else "Undefined",
            self.date_until.strftime("%Y-%m-%d") if self.date_until else "Undefined",
        )
