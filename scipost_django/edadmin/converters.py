__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls.converters import SlugConverter


class SubmissionStageSlugConverter(SlugConverter):
    def __init__(self):
        from submissions.models import Submission
        self.regex = "|".join(s for s in Submission.STAGE_SLUGS)
