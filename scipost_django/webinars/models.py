__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.conf import settings
from django.db import models


class Webinar(models.Model):
    """
    Online meeting.
    """

    name = models.CharField(max_length=256)
    slug = models.SlugField(allow_unicode=True, primary_key=True)
    description = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        ),
    )
    publicly_visible = models.BooleanField(default=False)
    date_and_time = models.DateTimeField()
    duration = models.DurationField(default=datetime.timedelta(minutes=60))
    link = models.URLField(max_length=512)

    class Meta:
        ordering = ["-date_and_time"]

    def __str__(self):
        return f"{self.name} ({self.date_and_time})"


class WebinarRegistration(models.Model):
    webinar = models.ForeignKey(
        "webinars.Webinar",
        on_delete=models.CASCADE,
        related_name="participants",
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    affiliation = models.CharField(max_length=256, blank=True)

    class Meta:
        ordering = [
            "-webinar__date_and_time",
            "last_name",
            "first_name",
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name} to {self.webinar}"
