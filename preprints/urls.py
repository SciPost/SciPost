__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

app_name = 'preprints'

urlpatterns = [
    url(r'^{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        views.preprint_pdf,
        name='pdf'),
]
