__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from datetime import datetime, date, timedelta
import uuid

from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Ceil, Coalesce, ExtractDay
from django.urls import reverse
from django.utils import timezone

from comments.behaviors import validate_file_extension, validate_max_file_size
from scipost.constants import TITLE_CHOICES

from .managers import JobOpeningQuerySet, WorkContractQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipost.models import Contributor


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


class WorkContract(models.Model):
    """
    Work contract associated with an employee, defining salary, work hours, and days off.
    """

    DAYS_OFF_FTE = 31  # paid days off per year for full-time employees
    HOURS_PER_WEEK_FTE = 38.0  # standard full-time occupation, at ~7.5h/day

    SALARY_TYPE_MONTHLY = "monthly"
    SALARY_TYPE_HOURLY = "hourly"
    SALARY_TYPE_CHOICES = (
        (SALARY_TYPE_MONTHLY, "Monthly Salary"),
        (SALARY_TYPE_HOURLY, "Hourly Wage"),
    )

    employee = models.ForeignKey["Contributor"](
        "scipost.Contributor",
        on_delete=models.CASCADE,
    )
    salary_type = models.CharField(
        max_length=16,
        choices=SALARY_TYPE_CHOICES,
        default=SALARY_TYPE_HOURLY,
    )
    pay_rate = models.FloatField(
        help_text="Monthly salary or hourly wage, depending on salary type.",
        default=20.00,
    )
    work_hours_week = models.DurationField(
        help_text="Number of work hours per week (e.g., 38 for full-time).",
        default=timedelta(hours=HOURS_PER_WEEK_FTE),
    )
    days_off = models.IntegerField(
        help_text="Number of paid days off per year.",
        default=DAYS_OFF_FTE,
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    objects = WorkContractQuerySet.as_manager()

    class Meta:
        default_related_name = "work_contracts"
        ordering = ["-start_date"]

    def __str__(self):
        text = f"{self.employee} employed"
        text += f" at {self.fte:.2} FTE"
        if self.start_date:
            text += f" from {self.start_date}"
        if self.end_date:
            text += f" to {self.end_date}"
        return text

    @property
    def current_period(self) -> tuple[date, date] | None:
        """
        Get the current period of the contract as a date range spanning a year.
        """
        today = datetime.now().date()

        years_past_start = (today - self.start_date).days // 365
        start_year = self.start_date.year + years_past_start
        period_start = self.start_date.replace(year=start_year)
        period_end = period_start.replace(year=start_year + 1) - timedelta(days=1)

        if self.end_date:
            if self.end_date < today:
                return None
            else:
                period_end = min(period_end, self.end_date)

        return (period_start, period_end)

    @property
    def fte(self) -> float:
        """
        Full-Time Employment (FTE) percentage based on work hours.
        """
        return round(self.work_hours_week / timedelta(hours=self.HOURS_PER_WEEK_FTE), 2)

    @property
    def work_hours_month(self) -> timedelta:
        """
        The equivalent number of work hours per month based on weekly work hours.
        Assumes 4 + 1/3 weeks per month (52 weeks per year).
        """
        return self.work_hours_week * (4 + 1 / 3)

    @property
    def work_hours_day(self) -> timedelta:
        """
        The equivalent number of work hours per day based on weekly work hours.
        Assumes a 5-day work week.
        """
        return self.work_hours_week / 5.0

    @property
    def days_off_in_period(self) -> int:
        """
        Calculate the number of paid days off for the current period.
        """

        if (current_period := self.current_period) is None:
            return 0

        work_year_start, work_year_end = current_period
        period_as_year_fraction = (work_year_end - work_year_start).days / 365
        days_off_per_period = self.days_off * period_as_year_fraction

        return int(days_off_per_period) + 1  # round up

    @property
    def days_off_remaining(self) -> int:
        """
        Calculate the number of remaining paid days off for the current year.
        """

        if (current_period := self.current_period) is None:
            return 0

        work_year_start, work_year_end = current_period

        used_days_off: int = (
            self.employee.unavailability_periods.all()
            .filter(start__gte=work_year_start, end__lte=work_year_end)
            .annotate(duration_in_days=ExtractDay(F("end") - F("start")))
            .aggregate(total_days_off=Coalesce(Sum("duration_in_days"), 0))
            .get("total_days_off", 0)
        )

        return max(0, self.days_off_in_period - used_days_off)
