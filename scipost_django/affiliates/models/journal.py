__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.validators import validate_unicode_slug
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
    homepage = models.URLField(max_length=256, blank=True)

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
    def get_balance_info(self):
        """
        For each publishing year, provide financial info.
        """
        maxyear = self.publications.first().publication_date.year
        minyear = self.publications.last().publication_date.year
        years = range(maxyear, minyear - 1, -1)
        balance_info = {}
        for year in years:
            nr_publications = self.publications.filter(
                publication_date__year=year).count()
            subsidy_tally = self.affiliatejournalyearsubsidy_set.filter(
                journal=self,
                year=year,
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
        return balance_info
