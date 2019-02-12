__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^test/(?P<pk>\d+)/$', views.TestView.as_view(), name='test'),
]
