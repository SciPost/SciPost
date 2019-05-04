__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'sponsors'

urlpatterns = [

    url(
        r'^$',
        views.sponsors,
        name="sponsors"
    ),
]
