__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [

    url(
        r'^$',
        views.sponsors,
        name="sponsors"
    ),
]