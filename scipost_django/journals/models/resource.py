__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from ..managers import PublicationResourceQuerySet


class PublicationResource(models.Model):
    TYPE_SOURCE_REPO = "source_repo"
    TYPE_RELEASE_ARCHIVE_REPO = "release_repo"
    TYPE_LIVE_REPO = "live_repo"
    TYPE_SUP_INFO = "supplemental_info"
    TYPE_CHOICES = (
        (TYPE_SOURCE_REPO, "Publication source files repository"),
        (TYPE_RELEASE_ARCHIVE_REPO, "Codebase release version (archive) repository"),
        (TYPE_LIVE_REPO, "Live (external) repository"),
        (TYPE_SUP_INFO, "Supplemental information"),
    )
    _type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    publication = models.ForeignKey(
        "journals.Publication",
        on_delete=models.CASCADE,
        related_name="resources",
    )
    url = models.URLField()
    comments = models.CharField(max_length=256, blank=True)
    deprecated = models.BooleanField(default=False)

    objects = PublicationResourceQuerySet.as_manager()

    def __str__(self):
        return (
            f"Resource for {self.publication.doi_label}: "
            f"{self.get__type_display()} at {self.url}"
        )
