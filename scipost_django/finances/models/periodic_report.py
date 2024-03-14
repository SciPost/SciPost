__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse
from django.utils import timezone


class PeriodicReportType(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.name


def periodic_report_upload_path(instance, filename):
    return f"uploads/finances/periodic_reports/{instance.for_year}/{filename}"


class PeriodicReport(models.Model):
    """
    Any form of report (annual, financial, administrative etc).
    """

    _type = models.ForeignKey(
        "finances.PeriodicReportType",
        on_delete=models.CASCADE,
    )
    _file = models.FileField(
        upload_to=periodic_report_upload_path,
        max_length=256,
    )
    created_on = models.DateTimeField(default=timezone.now)
    for_year = models.PositiveSmallIntegerField()

    class META:
        ordering = ["-for_year", "_type__name"]

    def __str__(self):
        return f"{self.for_year} {self._type}"

    def get_absolute_url(self):
        if self._file:
            return reverse("finances:periodicreport_file", kwargs={"pk": self.id})
