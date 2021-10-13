__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import requests

from django.contrib.sites.models import Site
from django.urls import reverse
from django.db import models
from django.http import Http404

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
        verbose_name='Preprint file', help_text='Preprint file for SciPost standalone preprints',
        upload_to='UPLOADS/PREPRINTS/%Y/%m/', max_length=200, blank=True)

    # Dates
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-identifier_w_vn_nr']


    def __str__(self):
        return 'Preprint {}'.format(self.identifier_w_vn_nr)

    def get_absolute_url(self):
        """Return either saved url or url to open the pdf."""
        if self.url:
            return self.url
        if self._file:
            return reverse('preprints:pdf', args=(self.identifier_w_vn_nr,))
        raise Http404

    def get_document(self):
        """
        Retrieve the preprint document itself, calling preprint server if necessary.
        """
        url = self.get_absolute_url()
        if url[0] == '/': # SciPost-hosted, add base url
            url = 'https://%s%s' % (Site.objects.get_current().domain, url)
        response = requests.get(url)
        if response.status_code != 200:
            raise PreprintDocumentNotFoundError(url)
        return response.content

    @property
    def citation_pdf_url(self):
        """Return the absolute URL of the pdf for the meta tag for Google Scholar."""
        if self._file: # means this is a SciPost-hosted preprint
            return "https://%s%s" % (Site.objects.get_current().domain, self.get_absolute_url())
        elif self.is_arXiv:
            return self.get_absolute_url().replace("/abs/", "/pdf/")
        else:
            return self.get_absolute_url()

    @property
    def is_arXiv(self):
        """Return True if this preprint is hosted on arXiv."""
        return 'arxiv.org' in self.url
