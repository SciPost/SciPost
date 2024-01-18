__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re
import requests

from django.urls import reverse
from django.db import models

from common.utils import get_current_domain
from submissions.exceptions import PreprintDocumentNotFoundError


class Preprint(models.Model):
    """
    A preprint object, either at SciPost or with link to external preprint server.

    If the instance is a SciPost preprint, the `_file` field should be filled.
    """

    # (arXiv) identifiers with/without version number
    identifier_w_vn_nr = models.CharField(max_length=128, unique=True, db_index=True)
    url = models.URLField(blank=True)

    # SciPost preprints only
    _file = models.FileField(
        verbose_name="Preprint file",
        help_text="Preprint file for SciPost standalone preprints",
        upload_to="UPLOADS/PREPRINTS/%Y/%m/",
        max_length=200,
        blank=True,
    )

    # Dates
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-identifier_w_vn_nr"]

    def __str__(self):
        return "Preprint {}".format(self.identifier_w_vn_nr)

    def get_absolute_url(self):
        """Return either saved url or url to open the pdf."""
        if self.url:
            return self.url
        if self._file:
            return reverse("preprints:pdf", args=(self.identifier_w_vn_nr,))
        return None

    def get_document(self):
        """
        Retrieve the preprint document itself, calling preprint server if necessary.
        """
        if self._file:  # SciPost-hosted,
            # return file directly since the url isn't yet publicly accessible
            return self._file.read()
        url = self.citation_pdf_url
        response = requests.get(url)
        if response.status_code != 200 or not response.headers.get("Content-Type") in [
            "application/pdf",
            "application/octet-stream",
        ]:
            raise PreprintDocumentNotFoundError(url)
        return response.content

    @property
    def citation_pdf_url(self):
        """Return the absolute URL of the pdf for the meta tag for Google Scholar."""
        if self._file:  # means this is a SciPost-hosted preprint
            return "https://%s%s" % (
                get_current_domain(),
                self.get_absolute_url(),
            )
        elif self.is_arXiv:
            return "%s.pdf" % self.get_absolute_url().replace("/abs/", "/pdf/")
        # Match SocArXiv preprints
        elif m := re.match(r"https://doi.org/10.31235/osf.io/(\w*?)$", self.url):
            return "https://osf.io/%s/download" % m.group(1)
        # Match ChemRxiv preprints
        elif m := re.match(r"https://doi.org/(10.26434/.+)$", self.url):
            r = requests.get(
                f"https://chemrxiv.org/engage/chemrxiv/public-api/v1/items/doi/"
                + self.identifier_w_vn_nr
            )
            return r.json().get("asset").get("original").get("url")
        else:
            return self.get_absolute_url()

    @property
    def has_file(self):
        if self._file:
            return True
        return False

    @property
    def is_arXiv(self):
        """Return True if this preprint is hosted on arXiv."""
        return "arxiv.org" in self.url
