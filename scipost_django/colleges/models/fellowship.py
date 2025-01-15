__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from scipost.behaviors import TimeStampedModel

from ..managers import FellowQuerySet

if TYPE_CHECKING:
    from colleges.models import FellowshipNomination
    from scipost.models import Contributor
    from django.db.models.manager import ManyToManyRelatedManager, RelatedManager


class Fellowship(TimeStampedModel):
    """A Fellowship gives access to the Submission Pool to Contributors.

    Editorial College Fellowship connects the Editorial College and Contributors,
    possibly with a limiting start/until date and/or a Proceedings event.

    The date range will effectively be used while determining 'the pool' for a specific
    Submission, so it has a direct effect on the submission date.
    """

    id: int

    nominations_vetoed: "ManyToManyRelatedManager[FellowshipNomination, Fellowship]"

    STATUS_REGULAR = "regular"
    STATUS_SENIOR = "senior"
    STATUS_GUEST = "guest"
    STATUS_CHOICES = (
        (STATUS_REGULAR, "Regular"),
        (STATUS_SENIOR, "Senior"),
        (STATUS_GUEST, "Guest"),
    )

    college = models.ForeignKey(
        "colleges.College", on_delete=models.PROTECT, related_name="fellowships"
    )

    contributor = models.ForeignKey["Contributor"](
        "scipost.Contributor", on_delete=models.CASCADE, related_name="fellowships"
    )

    start_date = models.DateField(null=True, blank=True)
    until_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_REGULAR
    )

    objects = FellowQuerySet.as_manager()

    class Meta:
        ordering = ["contributor__user__last_name"]
        unique_together = ("college", "contributor", "start_date", "until_date")

    def __str__(self):
        _str = self.contributor.__str__()
        if self.guest:
            _str += " (guest fellowship)"
        return _str

    @property
    def guest(self):
        return self.status == self.STATUS_GUEST

    @property
    def senior(self):
        return self.status == self.STATUS_SENIOR

    def get_absolute_url(self):
        """Return the admin fellowship page."""
        return reverse("colleges:fellowship_detail", kwargs={"pk": self.id})

    def sibling_fellowships(self):
        """Return all Fellowships that are directly related to the Fellow of this Fellowship."""
        return self.contributor.fellowships.all()

    def is_active(self):
        """Check if the instance is within start and until date."""
        today = datetime.date.today()
        if not self.start_date:
            if not self.until_date:
                return True
            return today <= self.until_date
        elif not self.until_date:
            return today >= self.start_date
        return today >= self.start_date and today <= self.until_date
