__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'proceedings'

urlpatterns = [
    # Proceedings
    url(r'^$', views.proceedings, name='proceedings'),
    url(r'^add/$', views.ProceedingsAddView.as_view(), name='proceedings_add'),
    url(r'^(?P<id>[0-9]+)/$', views.proceedings_details, name='proceedings_details'),
    url(r'^(?P<id>[0-9]+)/edit$', views.ProceedingsUpdateView.as_view(), name='proceedings_edit'),
]
