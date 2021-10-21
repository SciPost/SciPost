__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = 'petitions'

urlpatterns = [
    path(
        '<slug:slug>/verify_signature/<str:key>',
        views.verify_signature,
        name='verify_signature'
    ),
    path(
        '<slug:slug>',
        views.petition,
        name='petition'
    ),
]
