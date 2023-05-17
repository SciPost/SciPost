__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from django.contrib.auth.models import User
from profiles.models import Profile
from django.utils import timezone
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Value
from django.db.models.functions import Concat
from django.conf import settings

from .constants import (
    PRODUCTION_STREAM_STATUS,
    PRODUCTION_STREAM_INITIATED,
    PRODUCTION_EVENTS,
    EVENT_MESSAGE,
    EVENT_HOUR_REGISTRATION,
    PRODUCTION_STREAM_COMPLETED,
    PROOFS_STATUSES,
    PROOFS_UPLOADED,
    PROOFS_REPO_STATUSES,
    PROOFS_REPO_UNINITIALIZED,
)
from .managers import (
    ProductionStreamQuerySet,
    ProductionEventManager,
    ProofsQuerySet,
    ProductionUserQuerySet,
)
from .utils import proofs_id_to_slug

from finances.models import WorkLog
from scipost.storage import SecureFileStorage


class ProductionUser(models.Model):
    """
    Production Officers will have a ProductionUser object related to their account
    to relate all production related actions to.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        unique=True,
        related_name="production_user",
        null=True,
    )
    name = models.CharField(max_length=128, blank=True)

    objects = ProductionUserQuerySet.as_manager()

    def __str__(self):
        if self.user:
            return "%s, %s" % (self.user.last_name, self.user.first_name)
        return "%s (deactivated)" % self.name


class ProductionStream(models.Model):
    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="production_stream",
    )
    opened = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=32,
        choices=PRODUCTION_STREAM_STATUS,
        default=PRODUCTION_STREAM_INITIATED,
    )

    officer = models.ForeignKey(
        "production.ProductionUser",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="streams",
    )
    supervisor = models.ForeignKey(
        "production.ProductionUser",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="supervised_streams",
    )
    invitations_officer = models.ForeignKey(
        "production.ProductionUser",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="invitations_officer_streams",
    )

    work_logs = GenericRelation(WorkLog, related_query_name="streams")

    objects = ProductionStreamQuerySet.as_manager()

    class Meta:
        permissions = (
            ("can_work_for_stream", "Can work for stream"),
            ("can_perform_supervisory_actions", "Can perform supervisory actions"),
        )

    def __str__(self):
        return "{arxiv}, {title}".format(
            arxiv=self.submission.preprint.identifier_w_vn_nr,
            title=self.submission.title,
        )

    def get_absolute_url(self):
        return reverse("production:stream", args=(self.id,))

    @cached_property
    def total_duration(self):
        totdur = self.work_logs.aggregate(models.Sum("duration"))
        return totdur["duration__sum"]

    @cached_property
    def completed(self):
        return self.status == PRODUCTION_STREAM_COMPLETED

    @property
    def latest_activity(self):
        if self.events.last():
            return self.events.last().noted_on
        return self.closed or self.opened


class ProductionEvent(models.Model):
    stream = models.ForeignKey(ProductionStream, on_delete=models.CASCADE, related_name="events")
    event = models.CharField(max_length=64, choices=PRODUCTION_EVENTS, default=EVENT_MESSAGE)
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey("production.ProductionUser", on_delete=models.CASCADE, related_name="events")
    noted_to = models.ForeignKey(
        "production.ProductionUser",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="received_events",
    )
    duration = models.DurationField(blank=True, null=True)

    objects = ProductionEventManager()

    class Meta:
        ordering = ["noted_on"]

    def __str__(self):
        return "%s: %s" % (self.stream, self.get_event_display())

    def get_absolute_url(self):
        return self.stream.get_absolute_url()

    @cached_property
    def editable(self):
        return self.event in [EVENT_MESSAGE, EVENT_HOUR_REGISTRATION] and not self.stream.completed


def production_event_upload_location(instance, filename):
    submission = instance.production_event.stream.submission
    return "UPLOADS/PRODSTREAMS/{year}/{thread_hash_head}/{filename}".format(
        year=submission.submission_date.year,
        thread_hash_head=str(submission.thread_hash).partition("-")[0],
        filename=filename,
    )


class ProductionEventAttachment(models.Model):
    """
    An ProductionEventAttachment is in general used by authors to reply to a Proofs version
    with their version of the Proofs with comments.
    """

    production_event = models.ForeignKey(
        "production.ProductionEvent",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    attachment = models.FileField(upload_to=production_event_upload_location, storage=SecureFileStorage())

    def get_absolute_url(self):
        return reverse(
            "production:production_event_attachment_pdf",
            args=(
                self.production_event.stream.id,
                self.id,
            ),
        )


def proofs_upload_location(instance, filename):
    submission = instance.stream.submission
    return "UPLOADS/PROOFS/{year}/{thread_hash_head}/{filename}".format(
        year=submission.submission_date.year,
        thread_hash_head=str(submission.thread_hash).partition("-")[0],
        filename=filename,
    )


class Proofs(models.Model):
    """
    Proofs are directly related to a ProductionStream and Submission in SciPost.
    """

    attachment = models.FileField(upload_to=proofs_upload_location, storage=SecureFileStorage())
    version = models.PositiveSmallIntegerField(default=0)
    stream = models.ForeignKey("production.ProductionStream", on_delete=models.CASCADE, related_name="proofs")
    uploaded_by = models.ForeignKey("production.ProductionUser", on_delete=models.CASCADE, related_name="+")
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=PROOFS_STATUSES, default=PROOFS_UPLOADED)
    accessible_for_authors = models.BooleanField(default=False)

    objects = ProofsQuerySet.as_manager()

    class Meta:
        ordering = ["stream", "version"]
        verbose_name_plural = "Proofs"

    def get_absolute_url(self):
        return reverse("production:proofs_pdf", kwargs={"slug": self.slug})

    def __str__(self):
        return "Proofs {version} for Stream {stream}".format(version=self.version, stream=self.stream.submission.title)

    def save(self, *args, **kwargs):
        # Control Report count per Submission.
        if not self.version:
            self.version = self.stream.proofs.count() + 1
        return super().save(*args, **kwargs)

    @property
    def slug(self):
        return proofs_id_to_slug(self.id)


class ProofsRepository(models.Model):
    """
    ProofsRepository is a GitLab repository of Proofs for a Submission.
    """

    stream = models.OneToOneField(
        ProductionStream,
        on_delete=models.CASCADE,
        related_name="proofs_repository",
    )
    status = models.CharField(
        max_length=32,
        choices=PROOFS_REPO_STATUSES,
        default=PROOFS_REPO_UNINITIALIZED,
    )

    @property
    def name(self) -> str:
        """
        Return the name of the repository in the form of "id_lastname".
        """
        # Get the last name of the first author by getting the first author string from the submission
        first_author_str = self.stream.submission.authors_as_list[0]
        first_author_profile = (
            Profile.objects.annotate(
                full_name=Concat("first_name", Value(" "), "last_name")
            )
            .filter(full_name=first_author_str)
            .first()
        )
        if first_author_profile is None:
            first_author_last_name = first_author_str.split(" ")[-1]
        else:
            first_author_last_name = first_author_profile.last_name
            # Keep only the last of the last names
            first_author_last_name = first_author_last_name.split(" ")[-1]

        return "{preprint_id}_{last_name}".format(
            preprint_id=self.stream.submission.preprint.identifier_w_vn_nr,
            last_name=first_author_last_name,
        )

    @property
    def journal_abbrev(self) -> str:
        # The DOI label is used to determine the path of the repository and template
        return self.stream.submission.editorial_decision.for_journal.doi_label

    @property
    def journal_subdivision(self) -> str:
        """
        Return the subdivision of the repository depending on the journal type.
        Regular journals are subdivided per year and month,
        while proceedings are subdivided per year and conference.
        """

        # TODO: Removing the whitespace should be more standardised
        # Refactor: journal and year are common to both cases
        # perhaps it is best to only return the subdivision month/conference
        if proceedings_issue := self.stream.submission.proceedings:
            return "{journal}/{year}/{conference}".format(
                journal=self.journal_abbrev,
                year=self.stream.submission.proceedings.event_end_date.year,
                conference=proceedings_issue.event_suffix.replace(" ", ""),
            )
        else:
            # Get creation date of the stream
            # Warning: The month grouping of streams was done using the tasked date,
            # but should now instead be the creation (opened) date.
            opened_year, opened_month = self.stream.opened.strftime("%Y-%m").split("-")

            return "{journal}/{year}/{month}".format(
                journal=self.journal_abbrev,
                year=opened_year,
                month=opened_month,
            )

    @property
    def git_path(self) -> str:
        return "{ROOT}/Proofs/{journal_subdivision}/{repo_name}".format(
            ROOT=settings.GITLAB_ROOT,
            journal_subdivision=self.journal_subdivision,
            repo_name=self.name,
        )

    @property
    def template_path(self) -> str:
        """
        Return the path to the template repository.
        """
        if self.stream.submission.proceedings is not None:
            return "{ROOT}/Templates/{journal_subdivision}".format(
                ROOT=settings.GITLAB_ROOT,
                journal_subdivision=self.journal_subdivision,
            )
        else:
            return "{ROOT}/Templates/{journal}".format(
                ROOT=settings.GITLAB_ROOT,
                journal=self.journal_abbrev,
            )

    def __str__(self) -> str:
        return f"Proofs repo for {self.stream}"

    class Meta:
        verbose_name_plural = "proofs repositories"


@receiver(post_save, sender=ProductionStream)
def production_stream_create_proofs_repo(sender, instance, created, **kwargs):
    """
    When a ProductionStream instance is created, a ProofsRepository instance is created
    and linked to it.
    """
    if created:
        ProofsRepository.objects.create(
            stream=instance,
            status=PROOFS_REPO_UNINITIALIZED,
        )


post_save.connect(production_stream_create_proofs_repo, sender=ProductionStream)


@receiver(post_save, sender=ProofsRepository)
def advance_repo_on_gitlab(sender, instance, created, **kwargs):
    """
    When a ProofsRepository instance is created, run the advance_git_repos command on it.
    """
    if created:
        from django.core import management

        management.call_command(
            "advance_git_repos",
            id=instance.stream.submission.preprint.identifier_w_vn_nr,
        )


post_save.connect(advance_repo_on_gitlab, sender=ProofsRepository)
