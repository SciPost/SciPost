__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.VGMs, name='VGMs'),
    url(r'^VGM/(?P<VGM_id>[0-9]+)/$', views.VGM_detail, name='VGM_detail'),
    url(r'^feedback/(?P<VGM_id>[0-9]+)$', views.feedback, name='feedback'),
    url(r'^add_remark_on_feedback/(?P<VGM_id>[0-9]+)/(?P<feedback_id>[0-9]+)$',
        views.add_remark_on_feedback, name='add_remark_on_feedback'),
    url(r'^nominate_Fellow/(?P<VGM_id>[0-9]+)$', views.nominate_Fellow, name='nominate_Fellow'),
    url(r'^add_remark_on_nomination/(?P<VGM_id>[0-9]+)/(?P<nomination_id>[0-9]+)$',
        views.add_remark_on_nomination, name='add_remark_on_nomination'),
    url(r'^vote_on_nomination/(?P<nomination_id>[0-9]+)/(?P<vote>[AND])$',
        views.vote_on_nomination, name='vote_on_nomination'),
    url(r'^put_motion_forward/(?P<VGM_id>[0-9]+)$',
        views.put_motion_forward, name='put_motion_forward'),
    url(r'^add_remark_on_motion/(?P<motion_id>[0-9]+)$',
        views.add_remark_on_motion, name='add_remark_on_motion'),
    url(r'^vote_on_motion/(?P<motion_id>[0-9]+)/(?P<vote>[AND])$',
        views.vote_on_motion, name='vote_on_motion'),
]
