__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse

from series.managers import SeriesQuerySet


class Series(models.Model):
    """
    Anchor for a series of thematically-related Collections.
    """

    name = models.CharField(max_length=256, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        )
    )
    information = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
        blank=True,
    )
    image = models.ImageField(upload_to="series/images/", blank=True)
    container_journals = models.ManyToManyField(
        "journals.Journal", blank=True, related_name="contained_series"
    )

    objects = SeriesQuerySet.as_manager()

    @property
    def is_uniquely_contained(self):
        return self.container_journals.count() == 1

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("series:series_detail", kwargs={"slug": self.slug})


class Collection(models.Model):
    """
    A set of Publications which forms a coherent whole.
    """

    series = models.ForeignKey(
        "series.Series",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="collections",
    )
    name = models.CharField(max_length=256, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(
        blank=True,
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
    )
    event_start_date = models.DateField(null=True, blank=True)
    event_end_date = models.DateField(null=True, blank=True)
    event_details = models.TextField(
        blank=True,
        help_text=(
            "The details of the event, to be displayed as information "
            "about the collection in the paper."
        ),
    )
    image = models.ImageField(upload_to="series/collections/images/", blank=True)
    is_active = models.BooleanField(default=True)

    editor_considerations = models.TextField(
        blank=True,
        help_text=("Special rules enforced in this Collection, affecting the editors."),
    )

    enforce_expected_authors = models.BooleanField(
        default=True,
        help_text=(
            "If checked, only authors in the expected_authors "
            "list can submit to this collection."
        ),
    )
    expected_authors = models.ManyToManyField(
        "profiles.Profile", blank=True, related_name="collections_authoring"
    )
    expected_editors = models.ManyToManyField(
        "colleges.Fellowship", blank=True, related_name="collections_editing"
    )
    submissions = models.ManyToManyField(
        "submissions.Submission", blank=True, related_name="collections"
    )
    publications = models.ManyToManyField(
        "journals.Publication",
        through="series.CollectionPublicationsTable",
        blank=True,
        related_name="collections",
    )

    def __str__(self):
        return self.name

    @property
    def name_with_series(self):
        return f"{self.series.name} - {self.name}"

    def get_absolute_url(self):
        return reverse("series:collection_detail", kwargs={"slug": self.slug})

    def cleanup_ordering(self):
        """Ensure that order takes values 1, 2, ... [nr publications]."""
        for counter, cpt in enumerate(self.collectionpublicationstable_set.all()):
            cpt.order = counter + 1
            cpt.save()


class CollectionPublicationsTable(models.Model):
    collection = models.ForeignKey("series.Collection", on_delete=models.CASCADE)
    publication = models.ForeignKey("journals.Publication", on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = [
            "order",
        ]
        unique_together = ["collection", "order"]

    def __str__(self):
        return "In Collection %s: publication %s" % (
            str(self.collection),
            str(self.publication),
        )

    def save(self, *args, **kwargs):
        """Auto increment order number if not explicitly set."""
        if not self.order:
            self.order = self.collection.publications.count() + 1
        return super().save(*args, **kwargs)
