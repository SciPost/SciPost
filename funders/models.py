from django.db import models


class Funder(models.Model):
    """
    Funding info metadata is linked to funders from Crossref's
    Fundref registry.
    """
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Grant(models.Model):
    """
    An instance of a grant, award or other funding.
    In a Publication's metadata, all grants are listed
    in the Crossmark part of the metadata.
    """
    funder = models.ForeignKey(Funder, on_delete=models.CASCADE)
    number = models.CharField(max_length=64)
    recipient_name = models.CharField(max_length=64, blank=True, null=True)
    recipient = models.ForeignKey('scipost.Contributor', blank=True, null=True,
                                  on_delete=models.CASCADE)

    class Meta:
        ordering = ['funder', 'recipient', 'recipient_name', 'number']
        unique_together = ('funder', 'number')

    def __str__(self):
        grantstring = '%s, grant number %s' % (str(self.funder), self.number)
        if self.recipient:
            grantstring += ' (%s)' % str(self.recipient)
        elif self.recipient_name:
            grantstring += ' (%s)' % self.recipient_name
        return grantstring
