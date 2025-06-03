__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from profiles.models import Profile


class Topic(models.Model):
    """
    A Topic represents one of the nodes in the ontology.
    """

    name = models.CharField(max_length=256, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    tags = models.ManyToManyField("ontology.Tag", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ontology:topic_details", kwargs={"slug": self.slug})


class TopicInterest(models.Model):
    """
    An interest of a Profile in a Topic, either declared via a user action or inferred from their activity.
    Weights should be in the range [-1, 1], with 0 meaning no interest, -1 meaning strong disinterest, and 1 meaning strong interest.
    Automatic interests are inferred from the user's activity, and should not be modified by any user directly, only by the system.
    """

    SOURCE_MANUAL = "manual"
    SOURCE_AUTOMATIC = "automatic"
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, "Manual"),
        (SOURCE_AUTOMATIC, "Automatic"),
    ]

    profile = models.ForeignKey["Profile"]("profiles.Profile", on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="interests")
    weight = models.FloatField(
        default=1.0,
        help_text="Relative interest in the range [-1, 1], e.g. 0.4 or -0.3. A weight of (0/-1/1) means (no/dis/-) interest.",
    )
    source = models.CharField(
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
        max_length=16,
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        default_related_name = "topic_interests"
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "topic", "source"],
                name="unique_topic_interest_source",
            ),
            models.CheckConstraint(
                check=models.Q(weight__gte=-1) & models.Q(weight__lte=1),
                name="weight_range",
                violation_error_message="Weight must be in the range [-1, 1]",
            ),
        ]

    def __str__(self):
        verb = "interested" if self.weight > 0 else "disinterested"
        return f"{self.profile} is {verb} in {self.topic} ({self.weight})"
