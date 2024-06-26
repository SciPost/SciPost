__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import Q

from django.urls import reverse
from django.db import models
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.utils import timezone

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
from .managers import ProfileQuerySet, AffiliationQuerySet


class Profile(models.Model):
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

    title = models.CharField(max_length=4, choices=TITLE_CHOICES, default=TITLE_DR)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)

    first_name_original = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="First name (original)",
        help_text="Name in original script (if not using the Latin alphabet)",
    )
    last_name_original = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Last name (original)",
        help_text="Name in original script (if not using the Latin alphabet)",
    )

    orcid_authenticated = models.BooleanField(default=False)
    orcid_id = models.CharField(
        max_length=20, verbose_name="ORCID id", blank=True, validators=[orcid_validator]
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

    objects = ProfileQuerySet.as_manager()

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return "%s, %s %s" % (
            self.last_name,
            self.get_title_display() if self.title != None else "",
            self.first_name,
        )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name_original(self):
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
            f' ({",".join(r)})' if r else "",
        )

    @property
    def email(self):
        return getattr(self.emails.filter(primary=True).first(), "email", "")

    @property
    def has_active_contributor(self):
        has_active_contributor = False
        try:
            has_active_contributor = (
                self.contributor is not None and self.contributor.is_active
            )
        except Contributor.DoesNotExist:
            pass
        return has_active_contributor

    def get_absolute_url(self):
        return reverse("profiles:profile_detail", kwargs={"pk": self.id})

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

    @property
    def responsiveness_as_referee(self):
        """Simple stats on last 5 years' responsiveness as a referee."""
        invitations = self.refereeinvitation_set.all()
        if self.contributor:
            invitations = invitations | self.contributor.referee_invitations.all()

        invitations = invitations.distinct().filter(
            date_invited__gt=timezone.now() - datetime.timedelta(days=1825)
        )
        return {
            "sent": invitations.count(),
            "accepted": invitations.accepted().count(),
            "declined": invitations.declined().count(),
            "cancelled": invitations.filter(cancelled=True).count(),
            "fulfilled": invitations.filter(fulfilled=True).count(),
        }

    def has_competing_interest_with(self, profile):
        """
        Returns True if this Profile has a CompetingInterest with the given Profile.
        """
        from ethics.models import CompetingInterest

        return CompetingInterest.objects.filter(
            Q(profile=self, related_profile=profile)
            | Q(related_profile=self, profile=profile)
        ).exists()


class ProfileEmail(models.Model):
    """Any email related to a Profile instance."""

    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    email = models.EmailField()
    still_valid = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="profile_emails_added",
    )
    primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ["profile", "email"]
        ordering = ["-primary", "-still_valid", "email"]
        default_related_name = "emails"

    def __str__(self):
        return self.email


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
