__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class SubmissionRelatedObjectMixin:
    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'submission'):
            try:
                self.submission.touch()
            except AttributeError:
                pass
        return obj
