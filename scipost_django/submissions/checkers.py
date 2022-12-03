__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from checkers.base import ObjectCheckerAttrEqualsAttr

from .models import Submission


class SubmissionCheckResubmissionThreadAttr(ObjectCheckerAttrEqualsAttr):
    model = Submission
    filter_kwargs = {"is_resubmission_of__isnull": False}
    attribute1 = "thread_hash"
    attribute2 = "is_resubmission_of.thread_hash"

    def repair_object(self, object):
        object.thread_hash = object.is_resubmission_of.thread_hash
        object.save()
