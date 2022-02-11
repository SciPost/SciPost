__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import requests

from django.conf import settings
from django.db import models


class ValidatedAddress(models.Model):
    """
    Email address (lowercased) with related validation info.

    The Mailgun email validation v4 API is queried at least once per year
    and the response is saved as a related AddressValidation object.
    """

    address = models.EmailField(max_length=512, unique=True)  # as per Mailgun limit

    class Meta:
        ordering = [
            "address",
        ]

    def save(self, *args, **kwargs):
        self.address = self.address.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.address

    @property
    def is_good_for_sending(self):
        """
        Return the status of the latest Mailgun validation.
        """
        self.update_mailgun_validation()
        try:
            return self.validations.first().data["result"] in (
                "deliverable",
                "catch_all",
                "unknown",
            )
        except AttributeError:
            return False

    def update_mailgun_validation(self):
        """
        If no validation check within last year, call the Mailgun validation v4 API.
        """
        one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
        if not self.validations.filter(datestamp__gt=one_year_ago).exists():
            response = requests.get(
                "https://api.mailgun.net/v4/address/validate",
                auth=("api", settings.MAILGUN_API_KEY),
                params={"address": self.address},
            ).json()
            validation = AddressValidation(address=self, data=response)
            validation.save()


class AddressValidation(models.Model):
    """
    For a given ValidatedAddress, timestamped response from a Mailgun API validation v4 query.
    """

    address = models.ForeignKey(
        "apimail.ValidatedAddress", related_name="validations", on_delete=models.CASCADE
    )
    data = models.JSONField(default=dict)
    datestamp = models.DateField(default=datetime.date.today)

    class Meta:
        ordering = ["address__address", "-datestamp"]

    def __str__(self):
        return "%s: %s (%s)" % (self.address, self.data["result"], self.datestamp)
