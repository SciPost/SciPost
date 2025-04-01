__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import TYPE_CHECKING
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
import gitlab
import re

from guardian.shortcuts import assign_perm, remove_perm

from common.utils import latinise
from journals.models import Journal
from submissions.models.decision import EditorialDecision

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

if TYPE_CHECKING:
    from submissions.models import Submission
    from journals.models import Publication


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
    submission = models.OneToOneField["Submission"](
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="production_stream",
    )
    opened = models.DateTimeField(default=timezone.now)
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

    on_hold = models.BooleanField(default=False)

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

    def set_supervisor(
        self,
        supervisor: ProductionUser | None,
        performed_by: ProductionUser | None = None,
    ):
        # Remove permissions from previous supervisor
        if prev_supervisor := self.supervisor:
            remove_perm("can_perform_supervisory_actions", prev_supervisor.user, self)
            # Remove work permission only if they have no other role
            if prev_supervisor not in [self.officer, self.invitations_officer]:
                remove_perm("can_work_for_stream", prev_supervisor.user, self)

        self.supervisor = supervisor

        # Add permissions to new supervisor
        if supervisor:
            assign_perm("can_perform_supervisory_actions", supervisor.user, self)
            assign_perm("can_work_for_stream", supervisor.user, self)
            comments = " assigned Production Supervisor:"
        else:
            comments = f" removed Production Supervisor: {prev_supervisor}"

            self.add_event(
                event="assignment", by=performed_by, to=supervisor, comments=comments
            )

    def set_officer(
        self,
        officer: ProductionUser | None,
        performed_by: ProductionUser | None = None,
    ):
        # Remove permissions from previous officer
        if (prev_officer := self.officer) and (
            prev_officer not in [self.supervisor, self.invitations_officer]
        ):
            print("Removing permissions for", prev_officer.user)
            remove_perm("can_work_for_stream", prev_officer.user, self)

        self.officer = officer

        # Add permissions to new officer
        if officer:
            assign_perm("can_work_for_stream", officer.user, self)
            comments = " assigned Production Officer:"
        else:
            comments = f" removed Production Officer: {prev_officer}"

        self.add_event(
            event="assignment", by=performed_by, to=officer, comments=comments
        )

    def add_event(
        self,
        event,
        by: ProductionUser | None = None,
        comments=None,
        duration=None,
        to=None,
    ):
        by = by or ProductionUser.objects.filter(user__username="system").first()
        ProductionEvent.objects.create(
            stream=self,
            event=event,
            noted_by=by,
            noted_to=to,
            comments=comments,
            duration=duration,
        )

    @cached_property
    def total_duration(self):
        totdur = self.work_logs.aggregate(models.Sum("duration"))
        return totdur["duration__sum"]

    @cached_property
    def completed(self):
        return self.status == PRODUCTION_STREAM_COMPLETED

    @cached_property
    def in_stasis(self):
        return self.on_hold or (
            self.submission.editorial_decision.status
            == EditorialDecision.AWAITING_PUBOFFER_ACCEPTANCE
        )

    @property
    def latest_activity(self):
        if self.events.last():
            return self.events.last().noted_on
        return self.closed or self.opened


class ProductionEvent(models.Model):
    stream = models.ForeignKey(
        ProductionStream, on_delete=models.CASCADE, related_name="events"
    )
    event = models.CharField(
        max_length=64, choices=PRODUCTION_EVENTS, default=EVENT_MESSAGE
    )
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey(
        "production.ProductionUser", on_delete=models.CASCADE, related_name="events"
    )
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
        return (
            self.event in [EVENT_MESSAGE, EVENT_HOUR_REGISTRATION]
            and not self.stream.completed
        )


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
    attachment = models.FileField(
        upload_to=production_event_upload_location, storage=SecureFileStorage()
    )

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

    attachment = models.FileField(
        upload_to=proofs_upload_location, storage=SecureFileStorage()
    )
    version = models.PositiveSmallIntegerField(default=0)
    stream = models.ForeignKey(
        "production.ProductionStream", on_delete=models.CASCADE, related_name="proofs"
    )
    uploaded_by = models.ForeignKey(
        "production.ProductionUser", on_delete=models.CASCADE, related_name="+"
    )
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=16, choices=PROOFS_STATUSES, default=PROOFS_UPLOADED
    )
    accessible_for_authors = models.BooleanField(default=False)

    objects = ProofsQuerySet.as_manager()

    class Meta:
        ordering = ["stream", "version"]
        verbose_name_plural = "Proofs"

    def get_absolute_url(self):
        return reverse("production:proofs_pdf", kwargs={"slug": self.slug})

    def __str__(self):
        return "Proofs {version} for Stream {stream}".format(
            version=self.version, stream=self.stream.submission.title
        )

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

    PROOFS_REPO_UNINITIALIZED = "uninitialized"
    PROOFS_REPO_CREATED = "created"
    PROOFS_REPO_TEMPLATE_ONLY = "template_only"
    PROOFS_REPO_TEMPLATE_FORMATTED = "template_formatted"
    PROOFS_REPO_PRODUCTION_READY = "production_ready"
    PROOFS_REPO_STATUSES = (
        (PROOFS_REPO_UNINITIALIZED, "The repository does not exist"),
        (PROOFS_REPO_CREATED, "The repository exists but is empty"),
        (PROOFS_REPO_TEMPLATE_ONLY, "The repository contains the bare template"),
        (
            PROOFS_REPO_TEMPLATE_FORMATTED,
            "The repository contains the automatically formatted template",
        ),
        (PROOFS_REPO_PRODUCTION_READY, "The repository is ready for production"),
    )

    stream = models.OneToOneField["ProductionStream"](
        ProductionStream,
        on_delete=models.CASCADE,
        related_name="proofs_repository",
    )
    status = models.CharField(
        max_length=32,
        choices=PROOFS_REPO_STATUSES,
        default=PROOFS_REPO_UNINITIALIZED,
    )
    name = models.CharField(max_length=128, default="")

    def __str__(self):
        return self.name

    @staticmethod
    def _get_repo_name(stream) -> str:
        """
        Return the name of the repository in the form of "id_lastname".
        """
        # Get the last name of the first author by getting the first author string from the submission
        first_author_str = stream.submission.authors_as_list[0]
        first_author_profile = (
            Profile.objects.with_full_names()
            .filter(full_name_annot=first_author_str)
            .first()
        )
        if first_author_profile is None:
            first_author_last_name = first_author_str.split(" ")[-1]
        else:
            first_author_last_name = first_author_profile.last_name

        # Remove accents from the last name to avoid encoding issues
        # and join multiple last names into one
        first_author_last_name = latinise(first_author_last_name).strip()
        first_author_last_name = first_author_last_name.replace(" ", "-")

        return "{preprint_id}_{last_name}".format(
            preprint_id=stream.submission.preprint.identifier_w_vn_nr,
            last_name=first_author_last_name,
        )

    @property
    def journal_abbrev(self) -> str:
        # The DOI label is used to determine the path of the repository and template
        """
        Returns the journal abbreviation for publication. The journal is the
        one associated with the submission's editorial decision, or, in the event of
        a Selections paper, it is the flagship journal of the college.
        """

        # Guard against null editorial decision
        if not (decision := self.stream.submission.editorial_decision):
            raise ValueError("No (non-deprecated) editorial decision exists")

        decision_journal = decision.for_journal

        if "Selections" in decision_journal.name:
            paper_field = self.stream.submission.acad_field
            college = paper_field.colleges.order_by("order").first()
            flagship_journal = college.journals.order_by("list_order").first()
            return flagship_journal.doi_label
        else:
            return decision_journal.doi_label

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
                year=proceedings_issue.event_start_date.year,
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
    def git_url(self) -> str:
        return "https://{GITLAB_URL}/{git_path}".format(
            GITLAB_URL=settings.GITLAB_URL,
            git_path=self.git_path,
        )

    @property
    def git_ssh_clone_url(self) -> str:
        return "git:{GITLAB_URL}/{git_path}.git".format(
            GITLAB_URL=settings.GITLAB_URL,
            git_path=self.git_path,
        )

    @cached_property
    def template_paths(self) -> list[str]:
        """
        Return the list of paths to the various templates used for the proofs.
        """
        paths = ["{ROOT}/Templates/Base".format(ROOT=settings.GITLAB_ROOT)]

        if self.journal_abbrev.startswith("SciPost"):
            paths.append(
                "{ROOT}/Templates/BaseSciPost".format(ROOT=settings.GITLAB_ROOT)
            )

        # Determine whether to add the proceedings template or of some other journal
        if self.stream.submission.proceedings is not None:
            paths.append(
                "{ROOT}/Templates/{journal_subdivision}".format(
                    ROOT=settings.GITLAB_ROOT,
                    journal_subdivision=self.journal_subdivision,
                )
            )
        # Add extra paths for any collections associated with the submission
        # First add the base template for the series and then the collection
        elif collections := self.stream.submission.collections.all():
            for collection in collections:
                paths.append(
                    "{ROOT}/Templates/Series/{series}/Base".format(
                        ROOT=settings.GITLAB_ROOT,
                        series=collection.series.slug,
                        collection=collection.slug,
                    )
                )
                paths.append(
                    "{ROOT}/Templates/Series/{series}/{collection}".format(
                        ROOT=settings.GITLAB_ROOT,
                        series=collection.series.slug,
                        collection=collection.slug,
                    )
                )
        else:
            paths.append(
                "{ROOT}/Templates/{journal}".format(
                    ROOT=settings.GITLAB_ROOT,
                    journal=self.journal_abbrev,
                )
            )

        # Add the selected template if the submission is a Selections paper
        if "Selections" in self.stream.submission.editorial_decision.for_journal.name:
            paths.append("{ROOT}/Templates/Selected".format(ROOT=settings.GITLAB_ROOT))

        return paths

    def fetch_tex(self) -> str | None:
        """
        Fetches the TeX file of the publication, or of the proofs if not available.
        If both fail, returns None.
        """
        # Attempt to authenticate with GitLab
        try:
            gl = gitlab.Gitlab(
                "https://" + settings.GITLAB_URL,
                private_token=settings.GITLAB_KEY,
            )
            gl.auth()
        except:
            return None

        # Attempt to fetch the project from GitLab
        try:
            project = gl.projects.get(self.git_path)
        except:
            return None

        # Attempt to fetch the publication file
        try:
            publication_filename = [
                file["name"]
                for file in project.repository_tree()
                if re.findall("SciPost\w+(?:_\d+)+.tex", file["name"])
            ][0]
            publication_file = project.files.get(
                file_path=publication_filename, ref="main"
            )
            tex_contents = publication_file.decode().decode("utf-8")
            return tex_contents
        except:
            pass

        # Fall back to the submission's main file
        proofs_file = None
        for project_file in project.repository_tree(ref="main"):
            project_filename = project_file["name"]
            if project_filename.endswith(".tex") and self.name in project_filename:
                proofs_file = project.files.get(file_path=project_filename, ref="main")
                break

        if proofs_file is not None:
            tex_contents = proofs_file.decode().decode("utf-8")
            return tex_contents

        # If all else fails, return None
        return None

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
            status=ProofsRepository.PROOFS_REPO_UNINITIALIZED,
            name=ProofsRepository._get_repo_name(instance),
        )


post_save.connect(production_stream_create_proofs_repo, sender=ProductionStream)
