__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class SubmissionRelatedObjectMixin:
    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'submission'):
            self.submission.touch()
        return obj
