__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'markup'

urlpatterns = [

    url(
        r'^process/$',
        views.process,
        name='process'
    ),
]
