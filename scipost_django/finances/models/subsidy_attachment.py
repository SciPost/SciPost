__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import os

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse

from ..managers import SubsidyAttachmentQuerySet

from scipost.storage import SecureFileStorage


def subsidy_attachment_path(instance: "SubsidyAttachment", filename: str) -> str:
    """
    Save the uploaded SubsidyAttachments to country-specific folders.
    """
    if instance.subsidy is None:
        return "uploads/finances/subsidies/orphaned/%s" % filename

    return "uploads/finances/subsidies/{0}/{1}/{2}".format(
        instance.subsidy.date_from.strftime("%Y"),
        instance.subsidy.organization.country,
        filename,
    )


class SubsidyAttachment(models.Model):
    """
    A document related to a Subsidy.
    """

    KIND_AGREEMENT = "agreement"
    KIND_INVOICE = "invoice"
    KIND_PROOF_OF_PAYMENT = "proofofpayment"
    KIND_OTHER = "other"
    KIND_CHOICES = (
        (KIND_AGREEMENT, "Agreement"),
        (KIND_INVOICE, "Invoice"),
        (KIND_PROOF_OF_PAYMENT, "Proof of payment"),
        (KIND_OTHER, "Other"),
    )

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_INTERNAL = "internal"
    VISIBILITY_FINADMINONLY = "finadminonly"
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, "Publicly visible"),
        (VISIBILITY_INTERNAL, "Internal (admin, Org Contacts)"),
        (VISIBILITY_FINADMINONLY, "SciPost FinAdmin only"),
    )

    subsidy = models.ForeignKey["Subsidy"](
        "finances.Subsidy",
        related_name="attachments",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    attachment = models.FileField(
        max_length=256,
        upload_to=subsidy_attachment_path,
        storage=SecureFileStorage(),
    )

    git_url = models.URLField(
        blank=True, help_text="URL to the file's location in GitLab"
    )

    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES,
        default=KIND_AGREEMENT,
    )

    date = models.DateField(blank=True, null=True)

    description = models.TextField(blank=True)

    visibility = models.CharField(
        max_length=32,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_FINADMINONLY,
    )

    objects = SubsidyAttachmentQuerySet.as_manager()

    def __str__(self):
        return "%s, attachment to %s" % (self.attachment.name, self.subsidy)

    def get_absolute_url(self):
        if self.subsidy:
            return reverse(
                "finances:subsidy_attachment", kwargs={"attachment_id": self.id}
            )

    @property
    def filename(self):
        return os.path.basename(self.attachment.name)

    @property
    def publicly_visible(self):
        return self.visibility == self.VISIBILITY_PUBLIC

    def visible_to_user(self, current_user):
        if self.publicly_visible or current_user.has_perm(
            "scipost.can_manage_subsidies"
        ):
            return True
        if self.subsidy.organization.contactrole_set.filter(
            contact__dbuser=current_user
        ).exists():
            return True
        return False


# Delete attachment files with same name if they exist, allowing replacement without name change
@receiver(pre_save, sender=SubsidyAttachment)
def delete_old_attachment_file(sender, instance: SubsidyAttachment, **kwargs):
    """
    Replace existing file on update if a new one is provided.
    Move file to the new location if the subsidy changes.
    """
    if instance.pk and instance.attachment:
        old = SubsidyAttachment.objects.get(pk=instance.pk)
        if old is None or old.attachment is None:
            return

        # Delete old file if it is replaced
        if old.attachment != instance.attachment:
            old.attachment.delete(save=False)

        # Move file to new location if subsidy changes
        if old.subsidy != instance.subsidy:
            old_relative_path = old.attachment.name
            new_relative_path = subsidy_attachment_path(instance, instance.filename)

            instance.attachment.storage.save(new_relative_path, instance.attachment)
            instance.attachment.storage.delete(old_relative_path)
            instance.attachment.name = new_relative_path


@receiver(models.signals.post_delete, sender=SubsidyAttachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when its object is deleted.
    """
    if instance.attachment:
        instance.attachment.delete(save=False)
