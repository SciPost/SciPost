__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.db import models


class AddressBookEntry(models.Model):
    """
    Through field relating User and ValidatedAddress.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="address_book_entries",
    )

    address = models.ForeignKey(
        "apimail.ValidatedAddress",
        on_delete=models.CASCADE,
        related_name="address_book_entries",
    )

    description = models.CharField(
        max_length=512,
        blank=True,
        help_text="Description: [last name], [first name] or [org name] or other",
    )

    class Meta:
        ordering = ["user", "address"]
        verbose_name_plural = "Address book entries"
