__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


def submission_template_upload_path(instance, filename):
    return 'uploads/templates/{0}/{1}/{2}'.format(
        instance.journal.doi_label,
        instance.date.year,
        filename
    )

class SubmissionTemplate(models.Model):
    """
    Document template for submission to a given journal.
    """

    TYPE_LATEX_TGZ = 'latex-tgz'
    TYPE_DOCX = 'docx'
    TYPE_ODT = 'odt'
    TYPE_CHOICES = (
        (TYPE_LATEX_TGZ, 'LaTeX (gzipped tarball)'),
        (TYPE_DOCX, 'Office Open XML (.docx)'),
        (TYPE_ODT, 'OpenDocument Text (.odt)'),
    )

    journal = models.ForeignKey(
        'journals.Journal',
        on_delete=models.CASCADE,
        related_name='templates'
    )

    template_type = models.CharField(
        max_length=32,
        choices=TYPE_CHOICES,
        default=TYPE_LATEX_TGZ
    )

    template_file = models.FileField(
        upload_to=submission_template_upload_path,
        max_length=256
    )

    date = models.DateField()

    instructions = models.TextField(
        default='[To be filled in; you can use markup]'
    )

    class Meta:
        ordering = [
            'journal__doi_label',
            'date'
        ]

    def __str__(self):
        return 'Template for %s (%s) [%s]' % (
            self.journal.doi_label,
            self.get_template_type_display(),
            self.date
        )
