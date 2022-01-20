__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse


class Series(models.Model):
    """
    Anchor for a series of thematically-related Collections.
    """
    name = models.CharField(max_length=256, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(
        help_text=('You can use plain text, Markdown or reStructuredText; see our '
                   '<a href="/markup/help/" target="_blank">markup help</a> pages.')
    )
    information = models.TextField(
        help_text=('You can use plain text, Markdown or reStructuredText; see our '
                   '<a href="/markup/help/" target="_blank">markup help</a> pages.'),
        blank=True
    )
    image = models.ImageField(upload_to='series/images/', blank=True)
    container_journals = models.ManyToManyField(
        'journals.Journal',
        blank=True
    )

    class Meta:
        verbose_name_plural = 'series'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('series:series_detail', kwargs={'slug': self.slug})


class Collection(models.Model):
    """
    A set of Publications which forms a coherent whole.
    """
    series = models.ForeignKey(
        'series.Series',
        blank=True, null=True,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    description = models.TextField(
        blank=True,
        help_text=('You can use plain text, Markdown or reStructuredText; see our '
                   '<a href="/markup/help/" target="_blank">markup help</a> pages.')
    )
    event_start_date = models.DateField(null=True, blank=True)
    event_end_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='series/collections/images/', blank=True)

    expected_authors = models.ManyToManyField(
        'profiles.Profile',
        blank=True
    )
    submissions = models.ManyToManyField(
        'submissions.Submission',
        blank=True
    )
    publications = models.ManyToManyField(
        'journals.Publication',
        through='series.CollectionPublicationsTable',
        blank=True
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('series:collection_detail', kwargs={'slug': self.slug})


class CollectionPublicationsTable(models.Model):
    collection = models.ForeignKey(
        'series.Collection',
        on_delete=models.CASCADE
    )
    publication = models.ForeignKey(
        'journals.Publication',
        on_delete=models.CASCADE
    )
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order',]
        unique_together = ['collection', 'order']

    def __str__(self):
        return 'In Collection %s: publication %s' % (
            str(self.collection), str(self.publication))
