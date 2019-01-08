__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

from submissions.constants import SCIPOST_PREPRINT_W_VN_REGEX


urlpatterns = [
    url(r'^{regex}/$'.format(regex=SCIPOST_PREPRINT_W_VN_REGEX), views.preprint_pdf, name='pdf'),
]
