__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import random
import string

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import JSONField
from django.db import models
from django.template import loader
from django.urls import reverse

from common.utils import get_current_domain


class PublicationUpdate(models.Model):
    """
    Update to a Publication, for Crossmark.

    The Publication's authors are given authorship of any update by default.
    The license which is used (in Crossmark metadata) is the same as for the publication.
    """

    ADDENDUM = "addendum"
    CLARIFICATION = "clarification"
    CORRECTION = "correction"
    CORRIGENDUM = "corrigendum"
    ERRATUM = "erratum"
    CONCERN = "expression_of_concern"
    NEW_EDITION = "new_edition"
    NEW_VERSION = "new_version"
    PARTIAL_RETRACTION = "partial_retraction"
    REMOVAL = "removal"
    RETRACTION = "retraction"
    WITHDRAWAL = "withdrawal"
    TYPE_CHOICES = (
        (ADDENDUM, "Addendum"),
        (CLARIFICATION, "Clarification"),
        (CORRECTION, "Correction"),
        (CORRIGENDUM, "Corrigendum"),
        (ERRATUM, "Erratum"),
        (CONCERN, "Expression of concern"),
        (NEW_EDITION, "New edition"),
        (NEW_VERSION, "New version"),
        (PARTIAL_RETRACTION, "Partial_retraction"),
        (REMOVAL, "Removal"),
        (RETRACTION, "Retraction"),
        (WITHDRAWAL, "Withdrawal"),
    )

    publication = models.ForeignKey(
        "journals.Publication", on_delete=models.CASCADE, related_name="updates"
    )
    number = models.PositiveSmallIntegerField()
    update_type = models.CharField(
        max_length=32, choices=TYPE_CHOICES, default=CORRECTION
    )
    text = models.TextField(
        help_text=(
            "You can use plain text, Markdown or reStructuredText; see our "
            '<a href="/markup/help/" target="_blank">markup help</a> pages.'
        )
    )

    publication_date = models.DateField(verbose_name="publication date")

    doideposit_needs_updating = models.BooleanField(default=False)
    genericdoideposit = GenericRelation(
        "journals.GenericDOIDeposit", related_query_name="genericdoideposit"
    )
    doi_label = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["publication", "number"],
                name="unique_together_publication_number",
            ),
        ]
        ordering = ("-publication__publication_date", "-number")

    def __str__(self):
        return "%s-update-%d" % (self.publication.doi_label, self.number)

    @property
    def title(self):
        return "%s: %s" % (self.get_update_type_display(), self.publication.title)

    def create_doi_label(self):
        """Create a doi in the default format."""
        PublicationUpdate.objects.filter(id=self.id).update(
            doi_label="{}-update-{}".format(self.publication.doi_label, self.number)
        )

    @property
    def doi_string(self):
        return "%s-update-%s" % (self.publication.doi_string, self.number)

    @property
    def citation(self):
        return "%s (%s), doi:%s" % (
            self.publication.get_journal().name_abbrev,
            self.publication_date.strftime("%Y"),
            self.doi_string,
        )

    def get_absolute_url(self):
        return reverse(
            "scipost:publication_update_detail",
            kwargs={"doi_label": self.publication.doi_label, "update_nr": self.number},
        )

    def xml(self, doi_batch_id):
        """
        Create new XML structure (core, not header), return as a string.
        """
        # Render from template
        template = loader.get_template("xml/publication_update_crossref.html")
        context = {
            "domain": get_current_domain(),
            "update": self,
            "doi_batch_id": doi_batch_id,
            "deposit_email": settings.CROSSREF_DEPOSIT_EMAIL,
        }
        return template.render(context)
