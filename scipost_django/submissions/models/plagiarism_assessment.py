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
    date_set = models.DateTimeField(blank=True, null=True)
    comments_for_edadmin = models.TextField(blank=True)
    comments_for_authors = models.TextField(blank=True)

    @property
    def ongoing(self):
        return self.status == self.STATUS_ONGOING

    @property
    def passed(self):
        return self.status == self.STATUS_PASSED

    @property
    def failed(self):
        return self.status in [
            self.STATUS_FAILED_TEMPORARY,
            self.STATUS_FAILED_PERMANENT,
        ]


class InternalPlagiarismAssessment(PlagiarismAssessment):
    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="internal_plagiarism_assessment",
    )


class iThenticatePlagiarismAssessment(PlagiarismAssessment):
    submission = models.OneToOneField(
        "submissions.Submission",
        on_delete=models.CASCADE,
        related_name="iThenticate_plagiarism_assessment",
    )

    class Meta:
        verbose_name = "iThenticate plagiarism assessment"
        verbose_name_plural = "iThenticate plagiarism assessments"
