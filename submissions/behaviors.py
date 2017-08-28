class SubmissionRelatedObjectMixin:
    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        if hasattr(self, 'submission'):
            self.submission.touch()
        return obj
