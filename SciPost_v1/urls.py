"""SciPost_v1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

JOURNAL_REGEX = '(?P<doi_string>SciPostPhysProc|SciPostPhys)'

urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('sphinxdoc.urls')),
    url(r'^10.21468/%s/' % JOURNAL_REGEX, include('journals.urls.journal', namespace="journal")),
    url(r'^%s/' % JOURNAL_REGEX, include('journals.urls.journal', namespace="journal")),
    url(r'^', include('scipost.urls', namespace="scipost")),
    url(r'^contributor/', include('scipost.urls', namespace="scipost")),
    url(r'^commentaries/', include('commentaries.urls', namespace="commentaries")),
    url(r'^commentary/', include('commentaries.urls', namespace="commentaries")),
    url(r'^comments/', include('comments.urls', namespace="comments")),
    url(r'^journals/', include('journals.urls.general', namespace="journals")),

    url(r'^submissions/', include('submissions.urls', namespace="submissions")),
    url(r'^submission/', include('submissions.urls', namespace="submissions")),
    url(r'^theses/', include('theses.urls', namespace="theses")),
    url(r'^thesis/', include('theses.urls', namespace="theses")),
    url(r'^meetings/', include('virtualmeetings.urls', namespace="virtualmeetings")),
    url(r'^news/', include('news.urls', namespace="news")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
