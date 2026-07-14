__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import factory
import factory.fuzzy

from submissions.constants import PLAGIARISM_STATUSES

from ..models import iThenticateReport

from common.faker import LazyAwareDateOffset, fake, LazyObjectCount, LazyRandEnum


class iThenticateReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = iThenticateReport

    uploaded_time = fake.aware.date_time_this_year()
    processed_time = LazyAwareDateOffset("uploaded_time", "+10m")

    doc_id = LazyObjectCount(iThenticateReport, offset=1)
    part_id = LazyObjectCount(iThenticateReport, offset=1)

    percent_match = factory.fuzzy.FuzzyInteger(0, 100)
    status = LazyRandEnum(PLAGIARISM_STATUSES)
