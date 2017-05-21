from django.conf.urls import url

from . import views

urlpatterns = [

    url(r'^$', views.supporting_partners,
        name='partners'),
    url(r'^membership_request$', views.membership_request,
        name='membership_request'),
    url(r'^manage$', views.manage, name='manage'),
    url(r'^add_prospective_partner$', views.add_prospective_partner,
        name='add_prospective_partner'),
]
