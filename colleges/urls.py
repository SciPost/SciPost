from django.conf.urls import url

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

from . import views

urlpatterns = [
    # Fellowships
    url(r'^fellowships/$', views.fellowships, name='fellowships'),
    url(r'^fellowships/add$', views.fellowship_add, name='fellowship_add'),
    url(r'^fellowships/(?P<id>[0-9]+)/$', views.fellowship_detail, name='fellowship'),
    url(r'^fellowships/(?P<id>[0-9]+)/edit$', views.fellowship_edit, name='fellowship_edit'),
    url(r'^fellowships/(?P<id>[0-9]+)/terminate$', views.fellowship_terminate,
        name='fellowship_terminate'),
    url(r'^fellowships/submissions/{regex}/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_pool,
        name='submission'),
    url(r'^fellowships/submissions/{regex}/add$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_add_fellowship,
        name='submission_add_fellowship'),
    url(r'^fellowships/(?P<id>[0-9]+)/submissions/{regex}/remove$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.fellowship_remove_submission,
        name='fellowship_remove_submission'),
    url(r'^fellowships/(?P<id>[0-9]+)/submissions/add$',
        views.fellowship_add_submission, name='fellowship_add_submission'),
]
