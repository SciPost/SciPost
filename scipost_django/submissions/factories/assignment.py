__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import factory

from scipost.models import Contributor
from submissions.models.submission import Submission
from submissions.models import EditorialAssignment


class EditorialAssignmentFactory(factory.django.DjangoModelFactory):
    """
    An EditorialAssignmentFactory should always have a `submission` explicitly assigned. This will
    mostly be done using the post_generation hook in any SubmissionFactory.
    """

    submission = None
    to = factory.Iterator(Contributor.objects.all())
    status = factory.Iterator(Submission.SUBMISSION_STATUSES, getter=lambda c: c[0])
    date_created = factory.lazy_attribute(lambda o: o.submission.latest_activity)
    date_answered = factory.lazy_attribute(lambda o: o.submission.latest_activity)

    class Meta:
        model = EditorialAssignment
