__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django.urls import reverse

from guardian.shortcuts import assign_perm

from scipost.behaviors import TimeStampedModel
from scipost.models import Contributor
from commentaries.constants import COMMENTARY_PUBLISHED
from submissions.utils import clean_pdf

from .behaviors import validate_file_extension, validate_max_file_size
from .constants import (
    COMMENT_STATUS,
    STATUS_PENDING,
    STATUS_UNCLEAR,
    STATUS_INCORRECT,
    STATUS_NOT_USEFUL,
    STATUS_VETTED,
)
from .managers import CommentQuerySet


WARNING_TEXT = (
    "Warning: Rather use/edit `content_object` instead or be 100% sure you"
    " know what you are doing!"
)
US_NOTICE = "Warning: This field is out of service and will be removed in the future."


class Comment(TimeStampedModel):
    """A Comment is an unsollicited note, submitted by a Contributor.

    A Comment is pointed to a particular Publication, Report or in reply
    to an earlier Comment.
    """

    status = models.SmallIntegerField(default=STATUS_PENDING, choices=COMMENT_STATUS)
    vetted_by = models.ForeignKey(
        "scipost.Contributor",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="comment_vetted_by",
    )
    file_attachment = models.FileField(
        upload_to="uploads/comments/%Y/%m/%d/",
        blank=True,
        validators=[validate_file_extension, validate_max_file_size],
    )

    # A Comment is always related to another model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, help_text=WARNING_TEXT
    )
    object_id = models.PositiveIntegerField(help_text=WARNING_TEXT)
    content_object = GenericForeignKey()

    nested_comments = GenericRelation("comments.Comment", related_query_name="comments")

    # Author info
    is_author_reply = models.BooleanField(default=False)
    author = models.ForeignKey(
        "scipost.Contributor", on_delete=models.CASCADE, related_name="comments"
    )
    anonymous = models.BooleanField(default=False, verbose_name="Publish anonymously")

    # Ethics
    gen_ai_disclosures = GenericRelation(
        "ethics.GenAIDisclosure",
        object_id_field="object_id",
        content_type_field="content_type",
        related_query_name="comment",
    )

    # Categories:
    is_cor = models.BooleanField(default=False, verbose_name="correction/erratum")
    is_rem = models.BooleanField(default=False, verbose_name="remark")
    is_que = models.BooleanField(default=False, verbose_name="question")
    is_ans = models.BooleanField(default=False, verbose_name="answer to question")
    is_obj = models.BooleanField(default=False, verbose_name="objection")
    is_rep = models.BooleanField(default=False, verbose_name="reply to objection")
    is_val = models.BooleanField(
        default=False, verbose_name="validation or rederivation"
    )
    is_lit = models.BooleanField(
        default=False, verbose_name="pointer to related literature"
    )
    is_sug = models.BooleanField(
        default=False, verbose_name="suggestion for further work"
    )
    comment_text = models.TextField()
    remarks_for_editors = models.TextField(
        blank=True, verbose_name="optional remarks for the Editors only"
    )
    date_submitted = models.DateTimeField("date submitted", default=timezone.now)

    needs_doi = models.BooleanField(null=True, default=None)
    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation(
        "journals.GenericDOIDeposit", related_query_name="genericdoideposit"
    )
    doi_label = models.CharField(max_length=200, blank=True)
    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ["-date_submitted"]
        permissions = (("can_vet_comments", "Can vet submitted Comments"),)

    def __str__(self):
        text = "Anonymous"
        if not self.anonymous:
            text = self.author.user.first_name + " " + self.author.user.last_name
        return (
            text
            + " on "
            + self.date_submitted.strftime("%Y-%m-%d")
            + ", "
            + self.comment_text[:30]
        )

    def save(self, *args, **kwargs):
        super_save = super().save(*args, **kwargs)

        if self.file_attachment and self.anonymous:
            clean_pdf(self.file_attachment.path)

        return super_save

    @property
    def title(self):
        """Get title of Submission if Comment is pointed to Submission."""
        try:
            return self.content_object.title
        except:
            return self.content_type

    @cached_property
    def core_content_object(self):
        """Return object Comment is pointed to."""
        from commentaries.models import Commentary
        from submissions.models import Submission, Report
        from theses.models import ThesisLink

        to_object = self.content_object
        while True:
            # Loop because of possible nested relations
            if (
                isinstance(to_object, Submission)
                or isinstance(to_object, Commentary)
                or isinstance(to_object, ThesisLink)
            ):
                return to_object
            elif isinstance(to_object, Report):
                return to_object.submission
            elif isinstance(to_object, Comment):
                # Nested Comment.
                to_object = to_object.content_object
            else:
                raise Exception

    def all_nested_comments(self):
        """
        Returns a queryset of all nested comments (recursive).
        """
        qs = self.nested_comments.all()
        for c in qs:
            if c.nested_comments:
                qs = qs | c.all_nested_comments().all()
        return qs

    @property
    def is_vetted(self):
        """Check if Comment is vetted."""
        return self.status == STATUS_VETTED

    @property
    def is_unvetted(self):
        """Check if Comment is awaiting vetting."""
        return self.status == STATUS_PENDING

    @property
    def is_rejected(self):
        """Check if Comment is rejected."""
        return self.status in [STATUS_UNCLEAR, STATUS_INCORRECT, STATUS_NOT_USEFUL]

    @property
    def doi_string(self):
        if self.doi_label:
            return "10.21468/" + self.doi_label
        else:
            return None

    def create_doi_label(self):
        self.doi_label = "SciPost.Comment." + str(self.id)
        self.save()

    def get_absolute_url(self):
        return (
            self.content_object.get_absolute_url().split("#")[0]
            + "#comment_id"
            + str(self.id)
        )

    def get_attachment_url(self):
        return reverse("comments:attachment", args=(self.id,))

    @staticmethod
    def get_metadata_management_url():
        """Return url of the metadata management page for Comments."""
        return reverse("journals:manage_comment_metadata")

    def grant_permissions(self):
        # Import here due to circular import errors
        from submissions.models import Submission

        to_object = self.core_content_object
        if isinstance(to_object, Submission):
            # Add permissions for EIC only, the Vetting-group already has it!
            assign_perm(
                "comments.can_vet_comments", to_object.editor_in_charge.user, self
            )

    def get_author(self):
        """Return Contributor instance of object if not anonymous."""
        if not self.anonymous:
            return self.author
        return None

    def get_author_str(self):
        """Return author string if not anonymous."""
        author = self.get_author()
        if author:
            return "{} {}".format(
                author.profile.get_title_display(), author.user.last_name
            )
        return "Anonymous"

    @property
    def relation_to_published(self):
        """
        Check if the Comment relates to a SciPost-published object.
        If it is, return a dict with info on relation to the published object,
        based on Crossref's peer review content type.
        """
        # Import here due to circular import errors
        from submissions.models import Submission
        from journals.models import Publication
        from commentaries.models import Commentary

        to_object = self.core_content_object
        if isinstance(to_object, Submission):
            publication = Publication.objects.filter(
                accepted_submission__thread_hash=to_object.thread_hash
            )
            if publication:
                relation = {
                    "isReviewOfDOI": publication.doi_string,
                    "stage": "pre-publication",
                    "title": "Comment on " + to_object.preprint.identifier_w_vn_nr,
                }
                if self.is_author_reply:
                    relation["type"] = "author-comment"
                else:
                    relation["type"] = "community-comment"
                return relation
        if isinstance(to_object, Commentary):
            if to_object.type == COMMENTARY_PUBLISHED:
                relation = {
                    "isReviewOfDOI": to_object.pub_doi,
                    "stage": "post-publication",
                    "title": "Comment on " + to_object.pub_doi,
                }
                if self.is_author_reply:
                    relation["type"] = "author-comment"
                    relation["contributor_role"] = "author"
                else:
                    relation["type"] = "community-comment"
                    relation["contributor_role"] = "reviewer-external"
                return relation

        return None

    @property
    def citation(self):
        citation = ""
        if self.doi_string:
            if self.anonymous:
                citation += "Anonymous, "
            else:
                citation += "%s %s, " % (
                    self.author.user.first_name,
                    self.author.user.last_name,
                )

            if self.is_author_reply:
                citation += "SciPost Author Replies, "
            else:
                citation += "SciPost Comments, "
            citation += "Delivered %s, " % self.date_submitted.strftime("%Y-%m-%d")
            citation += "doi: %s" % self.doi_string
        return citation
