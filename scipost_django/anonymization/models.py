__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import enum
import uuid
from django.db import models

from anonymization.managers import AnonymousContributorManager, AnonymousProfileManager
from profiles.models import Profile
from scipost.models import Contributor

from typing import TYPE_CHECKING, Generic, TypeVar

TModel = TypeVar("TModel", bound=models.Model)


class AnonymousContributor(Contributor):
    """
    Represents an anonymous Contributor,
    using the same table through a proxy model.
    It implements a custom default manager to separate
    anonymous and eponymous contributors.
    """

    objects = AnonymousContributorManager()

    if TYPE_CHECKING:
        profile: "Profile | AnonymousProfile | None"

    def __str__(self):
        # Override the string representation because the default
        # uses the User model, now instantiated at runtime
        # with the same names, and provides no useful information.
        if self.profile:
            return f"{self.profile}"
        elif self.eponymization:
            return f"Anonymous Contributor {self.eponymization.uuid}"
        else:
            return super().__str__()

    class Meta:
        proxy = True
        verbose_name = "Anonymous Contributor"
        verbose_name_plural = "Anonymous Contributors"


class AnonymousProfile(Profile):
    """
    Represents an anonymous Profile,
    using the same table through a proxy model.
    It implements a custom default manager to separate
    anonymous and eponymous profiles.
    """

    objects = AnonymousProfileManager()

    if TYPE_CHECKING:
        # Reverse relation return cannot be None, it will just raise an error
        contributor: "Contributor | AnonymousContributor"

    class Meta:
        proxy = True
        verbose_name = "Anonymous Profile"
        verbose_name_plural = "Anonymous Profiles"


class AnonymizationStatus(enum.Enum):
    PENDING = "pending"
    LINKED = "linked"
    ANONYMIZED = "anonymized"
    ORPHANED = "orphaned"


class AnonymizationBase(models.Model, Generic[TModel]):
    """
    Base class for anonymization (record) models.
    Should contain a unique UUID field,
    a foreign key to the original object, and
    a one-to-one relationship to the anonymized object.
    """

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    if TYPE_CHECKING:
        original: models.ForeignKey[TModel | None]
        # This should be implemented in each subclass
        anonymous: models.OneToOneField[TModel | None]

    def __str__(self):
        match self.status:
            case AnonymizationStatus.PENDING:
                return f"Pending anonymization of {self.original}"
            case AnonymizationStatus.LINKED:
                return f"Anonymization of {self.original} as {self.anonymous}"
            case AnonymizationStatus.ANONYMIZED:
                return f"Anonymized {self.anonymous}"
            case AnonymizationStatus.ORPHANED:
                return "Orphaned anonymization"

    @property
    def status(self) -> AnonymizationStatus:
        """Return the status of the anonymization:
        - pending: original object exists, no anonymous version yet
        - linked: both original and anonymous objects exist
        - anonymized: anonymous object exists, original purged
        - orphaned: no original or anonymous object (should not happen)
        """
        match (self.original, self.anonymous):
            case (None, None):
                return AnonymizationStatus.ORPHANED
            case (None, _):
                return AnonymizationStatus.ANONYMIZED
            case (_, None):
                return AnonymizationStatus.PENDING
            case (_, _):
                return AnonymizationStatus.LINKED

    class Meta:
        abstract = True


class ProfileAnonymization(AnonymizationBase[Profile]):
    """
    Represents an anonymous profile replacing an eponymous one.
    """

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(original_id=models.F("anonymous_id")),
                name="original_anonymous_profile_different",
                violation_error_message="Anonymized profile must be different from the original profile.",
            ),
        ]

    original = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anonymizations",
    )
    anonymous = models.OneToOneField(
        AnonymousProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eponymization",
    )  # type: ignore - AnonymousProfile is a subclass of Profile


class ContributorAnonymization(AnonymizationBase[Contributor]):
    """
    Represents an anonymous contributor replacing an eponymous one.
    """

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(original_id=models.F("anonymous_id")),
                name="original_anonymous_contributor_different",
                violation_error_message="Anonymized contributor must be different from the original contributor.",
            ),
        ]

    original = models.ForeignKey(
        Contributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anonymizations",
    )
    anonymous = models.OneToOneField(
        AnonymousContributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eponymization",
    )  # type: ignore - AnonymousContributor is a subclass of Contributor
