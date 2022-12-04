__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class PlagiarismAssessment(models.Model):
    STATUS_ONGOING = "ongoing"
    STATUS_PASSED = "passed"
    STATUS_FAILED_TEMPORARY = "failed_temporary"
    STATUS_FAILED_PERMANENT = "failed_permanent"
    STATUS_CHOICES = (
        (STATUS_ONGOING, "Ongoing"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED_TEMPORARY, "Failed (temporary: author action needed)"),
        (STATUS_FAILED_PERMANENT, "Failed (permanent: not solvable)"),
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_ONGOING,
    )
    passed_on = models.DateTimeField(blank=True, null=True)
    comments_for_edadmin = models.TextField()
    comments_for_authors = models.TextField()

    @property
    def passed(self):
        return self.status == self.STATUS_PASSED


class InternalPlagiarismAssessment(PlagiarismAssessment):
    pass


class iThenticatePlagiarismAssessment(PlagiarismAssessment):
    class Meta:
        verbose_name = "iThenticate plagiarism assessment"
        verbose_name_plural = "iThenticate plagiarism assessments"
