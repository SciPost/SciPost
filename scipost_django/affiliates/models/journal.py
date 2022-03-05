__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import FileExtensionValidator, validate_unicode_slug
from django.db import models
from django.urls import reverse


def cost_default_value():
    return {"default": 400}


class AffiliateJournal(models.Model):
    """
    A Journal which piggybacks on SciPost's services.
    """

    publisher = models.ForeignKey(
        "affiliates.AffiliatePublisher",
        on_delete=models.CASCADE,
        related_name="journals",
    )

    name = models.CharField(max_length=256)

    short_name = models.CharField(max_length=256, default="")

    slug = models.SlugField(
        max_length=128,
        validators=[
            validate_unicode_slug,
        ],
        unique=True,
    )

    acad_field = models.ForeignKey(
        "ontology.AcademicField", on_delete=models.PROTECT, blank=True, null=True,
    )
    specialties = models.ManyToManyField(
        "ontology.Specialty", blank=True,
    )

    homepage = models.URLField(max_length=256, blank=True)

    logo_svg = models.FileField(
        upload_to="affiliates/journals/logos/",
        validators=[FileExtensionValidator(['svg'])],
        blank=True,
    )
    logo = models.ImageField(upload_to="affiliates/journals/logos/", blank=True)

    # Cost per publication information
    cost_info = models.JSONField(default=cost_default_value)

    class Meta:
        ordering = ["publisher", "name"]
        permissions = (("manage_journal_content", "Manage Journal content"),)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("affiliates:journal_detail", kwargs={"slug": self.slug})

    def cost_per_publication(self, year):
        try:
            return int(self.cost_info[str(year)])
        except KeyError:
            return int(self.cost_info["default"])

    @property
    def balance_info(self):
        return self.get_balance_info()

    def get_balance_info(self, organization=None):
        """
        For each publishing year, provide financial info.
        """
        publications = self.publications.all()
        subsidies = self.affiliatejournalyearsubsidy_set.all()
        if organization:
            publications = publications.filter(
                pubfractions__organization=organization
            )
            subsidies = subsidies.filter(organization=organization)
        if not publications:
            return {}
        maxyear = publications.first().publication_date.year
        minyear = publications.last().publication_date.year
        years = range(maxyear, minyear - 1, -1)
        balance_info = {}
        for year in years:
            nr_publications = publications.filter(
                publication_date__year=year).count()
            subsidy_tally = subsidies.filter(
                year=year
            ).aggregate(models.Sum("amount"))["amount__sum"]
            if not subsidy_tally:
                subsidy_tally = 0
            balance_info[year] = {
                "nr_publications": nr_publications,
                "unit_cost": self.cost_per_publication(year),
                "expenditure": nr_publications * self.cost_per_publication(year),
                "subsidies": subsidy_tally,
                "balance": (subsidy_tally -
                            nr_publications * self.cost_per_publication(year)),
            }
            if organization:
                from ..models import AffiliatePubFraction
                sum_pubfracs = AffiliatePubFraction.objects.filter(
                    publication__journal=self,
                    organization=organization,
                    publication__publication_date__year=year,
                ).aggregate(models.Sum("fraction"))["fraction__sum"]
                if not sum_pubfracs:
                    sum_pubfracs = 0
                balance_info[year]["pubfractions"] = sum_pubfracs
                balance_info[year][
                    "expenditure"
                ] = int(sum_pubfracs * self.cost_per_publication(year))
                balance_info[year][
                    "balance"
                ] = int(subsidy_tally - sum_pubfracs * self.cost_per_publication(year))
        return balance_info
