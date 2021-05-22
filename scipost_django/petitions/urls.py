__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'petitions'

urlpatterns = [
    url(r'^(?P<slug>[-\w]+)/verify_signature/(?P<key>.+)$',
        views.verify_signature, name='verify_signature'),
    url(r'^(?P<slug>[-\w]+)$', views.petition, name='petition'),
]
