__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.utils.html import format_html


def get_current_year():
    return datetime.date.today().year


class AffiliateJournalYearSubsidy(models.Model):
    """
    A subsidy given to an AffiliateJournal in a particular year.
    """

    journal = models.ForeignKey(
        "affiliates.AffiliateJournal", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    description = models.TextField()
    amount = models.PositiveIntegerField(help_text="in &euro; (rounded)")
    year = models.PositiveSmallIntegerField(default=get_current_year)

    class Meta:
        verbose_name_plural = "year_subsidies"
        ordering = ["journal", "-year", "organization"]

    def __str__(self):
        return format_html(
            f"{self.year}: &euro;{self.amount} from {self.organization}, "
            f"for {self.description}"
        )
