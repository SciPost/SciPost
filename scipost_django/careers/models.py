__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone

from comments.behaviors import validate_file_extension, validate_max_file_size
from scipost.constants import TITLE_CHOICES

from .managers import JobOpeningQuerySet


class JobOpening(models.Model):
    """
    Information on a job opening.
    """

    DRAFTED = "drafted"
    VISIBLE = "visible"
    CLOSED = "closed"
    JOBOPENING_STATUSES = (
        (DRAFTED, "Drafted (not publicly visible)"),
        (VISIBLE, "Publicly visible"),
        (CLOSED, "Closed"),
    )
    slug = models.SlugField()
    announced = models.DateField()
    title = models.CharField(max_length=128)
    short_description = models.TextField()
    description = models.TextField()
    application_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=JOBOPENING_STATUSES)

    objects = JobOpeningQuerySet.as_manager()

    class Meta:
        ordering = ["-announced"]

    def __str__(self):
        return "%s (%s)" % (self.title, self.slug)

    def get_absolute_url(self):
        return reverse("careers:job_opening_detail", kwargs={"slug": self.slug})


class JobApplication(models.Model):
    """
    Filled by a candidate to a specific job.
    """

    RECEIVED = "received"
    VERIFIED = "verified"
    WITHDRAWN = "withdrawn"
    TURNEDDOWN = "turneddown"
    SHORTLISTED = "shortlisted"
    NOTSELECTED = "notselected"
    SELECTED = "selected"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    JOBAPP_STATUSES = (
        (RECEIVED, "Application received"),
        (VERIFIED, "Application received, email has been verified by applicant"),
        (TURNEDDOWN, "Applicant has not been shortlisted for the position"),
        (SHORTLISTED, "Applicant has been shortlisted for the position"),
        (NOTSELECTED, "Applicant has not been selected for the position"),
        (SELECTED, "Applicant has been selected for the position"),
        (ACCEPTED, "Applicant has accepted job offer"),
        (DECLINED, "Applicant has turned down job offer"),
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16, choices=JOBAPP_STATUSES)
    last_updated = models.DateTimeField(default=timezone.now)
    job_opening = models.ForeignKey(
        "careers.JobOpening", on_delete=models.CASCADE, related_name="job_applications"
    )
    date_received = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(
        help_text=(
            "The email address to which we will send a confirmation of reception "
            "of this application (you will need to click the verification link "
            "in that email once your receive it), and at which we can contact you "
            "throughout the selection process"
        )
    )
    motivation = models.FileField(
        upload_to="uploads/job_applications/%Y/%m/",
        validators=[validate_file_extension, validate_max_file_size],
        help_text=(
            "Please describe your motivations for applying, and "
            "your qualifications for this particular job (pdf file)"
        ),
    )
    cv = models.FileField(  # pylint: disable=C0103
        upload_to="uploads/job_applications/%Y/%m/",
        validators=[validate_file_extension, validate_max_file_size],
        help_text=(
            "Your curriculum vitae, including details of training and "
            "skills pertinent to this particular job (pdf file)"
        ),
    )

    class Meta:
        ordering = ["-job_opening__announced", "last_name"]

    def __str__(self):
        return "%s: %s, %s" % (self.job_opening.slug, self.last_name, self.first_name)

    def get_absolute_url(self):
        return reverse("careers:job_application_detail", kwargs={"uuid": self.uuid})
