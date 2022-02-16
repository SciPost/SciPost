__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse

from scipost.behaviors import TimeStampedModel
from scipost.constants import SCIPOST_APPROACHES
from scipost.fields import ChoiceArrayField

from .constants import COMMENTARY_TYPES
from .managers import CommentaryManager


class Commentary(TimeStampedModel):
    """
    A Commentary page for a given publication.
    """

    requested_by = models.ForeignKey(
        "scipost.Contributor",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="requested_commentaries",
    )
    vetted = models.BooleanField(default=False)
    vetted_by = models.ForeignKey(
        "scipost.Contributor", blank=True, null=True, on_delete=models.CASCADE
    )
    type = models.CharField(max_length=9, choices=COMMENTARY_TYPES)

    # Ontology-based semantic linking
    acad_field = models.ForeignKey(
        "ontology.AcademicField", on_delete=models.PROTECT, related_name="commentaries"
    )
    specialties = models.ManyToManyField(
        "ontology.Specialty", related_name="commentaries"
    )
    topics = models.ManyToManyField("ontology.Topic", blank=True)
    approaches = ChoiceArrayField(
        models.CharField(max_length=24, choices=SCIPOST_APPROACHES),
        blank=True,
        null=True,
        verbose_name="approach(es) [optional]",
    )
    open_for_commenting = models.BooleanField(default=True)

    # Article/publication data
    title = models.CharField(max_length=300)
    arxiv_identifier = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="arXiv identifier (including version nr)",
    )
    arxiv_link = models.URLField(
        verbose_name="arXiv link (including version nr)", blank=True
    )
    pub_DOI = models.CharField(
        max_length=200, verbose_name="DOI of the original publication", blank=True
    )
    pub_DOI_link = models.URLField(
        verbose_name="DOI link to the original publication", blank=True
    )
    metadata = models.JSONField(default=dict, blank=True, null=True)
    arxiv_or_DOI_string = models.CharField(
        max_length=100,
        verbose_name="string form of arxiv nr or" " DOI for commentary url",
    )
    scipost_publication = models.OneToOneField(
        "journals.Publication",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="commentary",
    )

    # Authors which have been mapped to contributors:
    author_list = models.CharField(max_length=1000)
    authors = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="commentaries"
    )
    authors_claims = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="claimed_commentaries"
    )
    authors_false_claims = models.ManyToManyField(
        "scipost.Contributor", blank=True, related_name="false_claimed_commentaries"
    )
    journal = models.CharField(max_length=300, blank=True)
    volume = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True)
    pub_date = models.DateField(
        verbose_name="date of original publication", blank=True, null=True
    )
    pub_abstract = models.TextField(verbose_name="abstract")

    # Comments can be added to a Commentary
    comments = GenericRelation("comments.Comment", related_query_name="commentaries")

    objects = CommentaryManager()

    class Meta:
        verbose_name_plural = "Commentaries"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("commentaries:commentary", args=(self.arxiv_or_DOI_string,))

    def parse_links_into_urls(self, commit=True):
        """Takes the arXiv nr or DOI and turns it into the urls"""
        if self.pub_DOI:
            self.arxiv_or_DOI_string = self.pub_DOI
            self.pub_DOI_link = "https://doi.org/" + self.pub_DOI
        elif self.arxiv_identifier:
            self.arxiv_or_DOI_string = "arXiv:" + self.arxiv_identifier
            self.arxiv_link = "https://arxiv.org/abs/" + self.arxiv_identifier

        if commit:
            self.save()
