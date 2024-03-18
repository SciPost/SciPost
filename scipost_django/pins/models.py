__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey

from .managers import NotesQuerySet


class Note(models.Model):
    """
    A note regarding a (generic) object.
    """

    class Meta:
        ordering = ("-created",)
        default_related_name = "notes"

    VISIBILITY_PRIVATE = "self"
    VISIBILITY_INTERNAL = "internal"
    VISIBILITY_PUBLIC = "public"  # Notes for everyone
    VISIBILITY_CHOICES = (
        (VISIBILITY_PRIVATE, "Private"),  # For creator only
        (VISIBILITY_INTERNAL, "Internal"),  # For group of object managers
        (VISIBILITY_PUBLIC, "Public"),  # For everyone
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    visibility = models.CharField(
        max_length=10,
        default=VISIBILITY_PRIVATE,
        choices=VISIBILITY_CHOICES,
    )

    regarding_content_type = models.ForeignKey(
        "contenttypes.ContentType",
        on_delete=models.CASCADE,
    )
    regarding_object_id = models.PositiveIntegerField(blank=True, null=True)
    regarding = GenericForeignKey("regarding_content_type", "regarding_object_id")

    author = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = NotesQuerySet.as_manager()

    def __str__(self):
        return self.title


class Pin(models.Model):
    """
    A pin associates a note with a user, making it visible in their task list.
    """

    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    due_date = models.DateField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pin of {self.note} for {self.user}"
