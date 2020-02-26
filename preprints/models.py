__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import reverse
from django.db import models
from django.http import Http404


class Preprint(models.Model):
    """A link with arXiv or standalone/SciPost-hosted preprint.

    If the instance is a SciPost preprint, the `_file` and `scipost_preprint_identifier` fields
    should be filled. Otherwise, these fields should be left blank.
    """

    # (arXiv) identifiers with/without version number
    identifier_w_vn_nr = models.CharField(max_length=25, unique=True, db_index=True)
    identifier_wo_vn_nr = models.CharField(max_length=25)
    vn_nr = models.PositiveSmallIntegerField(verbose_name='Version number', default=1)
    url = models.URLField(blank=True)

    # SciPost-preprints only
    scipost_preprint_identifier = models.PositiveIntegerField(
        verbose_name='SciPost preprint ID',
        null=True, blank=True, help_text='Unique identifier for SciPost standalone preprints')
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

    @property
    def citation_pdf_url(self):
        """Return the absolute URL of the pdf for the meta tag for Google Scholar."""
        if self._file: # means this is a SciPost-hosted preprint
            return "https://scipost.org%s" % self.get_absolute_url()
        return self.get_absolute_url().replace("/abs/", "/pdf/")
