__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse
from django.db import models
from django.http import Http404


class Preprint(models.Model):
    """A link with ArXiv or standalone/SciPost-hosted preprint.

    If the instance is a scipost preprint, the `_file` and `scipost_preprint_identifier` fields
    should be filled. Else, these fields should be left blank.
    """

    submission = models.OneToOneField('submissions.Submission')

    # (ArXiv) identifiers with/without version number
    # identifier_w_vn_nr = models.CharField(max_length=25, blank=True)
    scipost_preprint_identifier = models.PositiveIntegerField(null=True, blank=True)
    identifier_wo_vn_nr = models.CharField(max_length=25, blank=True)
    vn_nr = models.PositiveSmallIntegerField(default=1)
    url = models.URLField()

    _file = models.FileField(upload_to='UPLOADS/PREPRINTS/%Y/%m/', max_length=200, blank=True)

    # Dates
    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Preprint {}'.format(self.identifier_w_vn_nr)

    def get_absolute_url(self):
        if self.url:
            return self.url
        if self._file:
            return reverse('preprints:pdf', self.identifier_w_vn_nr)
        raise Http404

    @property
    def identifier_w_vn_nr(self):
        return '{}v{}'.format(self.identifier_wo_vn_nr, self.vn_nr)
