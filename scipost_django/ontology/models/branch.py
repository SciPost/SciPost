_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

class Branch(models.Model):
    """
    A principal division in the tree of knowledge.
    """

    name = models.CharField(max_length=128)

    slug = models.SlugField(unique=True, allow_unicode=True)

    order = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = [
            "order",
        ]
        verbose_name_plural = "branches"

    def __str__(self):
        return self.name

    @property
    def journals(self):
        from journals.models import Journal
        return Journal.objects.filter(college__acad_field__branch=self.id)

    @property
    def submissions(self):
        from submissions.models import Submission
        return Submission.objects.public_latest().filter(acad_field__branch=self.id)
