__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from abc import abstractmethod
from uuid import uuid4
from django.db import models

from typing import TYPE_CHECKING, TypeVar

TModel = TypeVar("TModel", bound=models.Model)

if TYPE_CHECKING:
    from .models import AnonymizationBase
    from django.db.models.manager import RelatedManager


class AnonymizableObjectMixin(models.Model):
    """
    Mixin to denote that an object can be anonymized.
    Provides a boolean field to indicate whether the object is anonymous,
    and references to anonymizations and its singular eponymization.
    """

    is_anonymous = models.BooleanField(default=False)

    if TYPE_CHECKING:
        eponymization: AnonymizationBase | None
        anonymizations: RelatedManager[AnonymizationBase]

    @property
    def prefer_eponymous(self) -> "models.Model":
        """
        Returns the original object if it exists.
        """
        try:
            return self.eponymization.original or self
        except (self.__class__.DoesNotExist, AttributeError):
            return self

    @abstractmethod
    def anonymize(self, uuid_str: str | None = None) -> "AnonymizationBase":
        """
        Creates an anonymous object of the same type,
        and returns the anonymization record for it.
        """
        uuid_str = str(uuid4()) if uuid_str is None else uuid_str
        record = self.anonymizations.create(
            uuid=uuid_str,
            original=self,
            anonymous=self.create_anonymous(uuid_str=uuid_str),
        )
        return record

    @classmethod
    @abstractmethod
    def create_anonymous(cls: type[TModel], uuid_str: str | None) -> TModel:
        """
        Creates an anonymous version of the object using the given UUID string.
        If no UUID string is provided, a new UUID will be generated.

        This method *does not* create a record of the anonymization.
        If a record is desired, use the `anonymize` method instead,
        which calls this method and creates the record.
        """
        if uuid_str is None:
            uuid_str = str(uuid4())

    class Meta:
        abstract = True
