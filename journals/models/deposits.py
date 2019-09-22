__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models

from journals.models import Publication


class Deposit(models.Model):
    """
    Each time a Crossref deposit is made for a Publication,
    a Deposit object instance is created containing the Publication's
    current version of the metadata_xml field.
    All deposit history is thus contained here.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=40)
    doi_batch_id = models.CharField(max_length=40)
    metadata_xml = models.TextField(blank=True)
    metadata_xml_file = models.FileField(blank=True, null=True, max_length=512)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response_text = models.TextField(blank=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        _str = ''
        if self.deposition_date:
            _str += '%s for ' % self.deposition_date.strftime('%Y-%m-%D')
        return _str + self.publication.doi_label


class DOAJDeposit(models.Model):
    """
    For the Directory of Open Access Journals.
    """
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    timestamp = models.CharField(max_length=40)
    metadata_DOAJ = JSONField()
    metadata_DOAJ_file = models.FileField(blank=True, null=True, max_length=512)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response_text = models.TextField(blank=True, null=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        verbose_name = 'DOAJ deposit'

    def __str__(self):
        return ('DOAJ deposit for ' + self.publication.doi_label)


class GenericDOIDeposit(models.Model):
    """
    Instances of this class represent Crossref deposits for non-publication
    objects such as Reports, Comments etc.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    timestamp = models.CharField(max_length=40, default='')
    doi_batch_id = models.CharField(max_length=40, default='')
    metadata_xml = models.TextField(blank=True, null=True)
    deposition_date = models.DateTimeField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    deposit_successful = models.NullBooleanField(default=None)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return 'GenericDOIDeposit for %s %s' % (self.content_type, str(self.content_object))
