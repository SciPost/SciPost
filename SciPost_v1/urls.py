from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

from ajax_select import urls as ajax_select_urls
from rest_framework import routers

from news.viewsets import NewsItemViewSet
from journals.constants import REGEX_CHOICES

# Journal URL Regex
JOURNAL_REGEX = '(?P<doi_label>%s)' % REGEX_CHOICES


# API Routing
router = routers.SimpleRouter()
router.register(r'news', NewsItemViewSet)
urlpatterns = router.urls


# Base URLs
urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax_select/', include(ajax_select_urls)),
    url(r'^api/', include(router.urls, namespace='api')),
    url(r'^docs/', include('sphinxdoc.urls')),
    url(r'^10.21468/%s/' % JOURNAL_REGEX, include('journals.urls.journal', namespace="journal")),
    url(r'^%s/' % JOURNAL_REGEX, include('journals.urls.journal', namespace="_journal")),
    url(r'^', include('scipost.urls', namespace="scipost")),
    url(r'^affiliations/', include('affiliations.urls', namespace="affiliations")),
    url(r'^colleges/', include('colleges.urls', namespace="colleges")),
    url(r'^commentaries/', include('commentaries.urls', namespace="commentaries")),
    url(r'^commentary/', include('commentaries.urls', namespace="_commentaries")),
    url(r'^comments/', include('comments.urls', namespace="comments")),
    url(r'^funders/', include('funders.urls', namespace="funders")),
    url(r'^finances/', include('finances.urls', namespace="finances")),
    url(r'^invitations/', include('invitations.urls', namespace="invitations")),
    url(r'^journals/', include('journals.urls.general', namespace="journals")),
    url(r'^mailing_list/', include('mailing_lists.urls', namespace="mailing_lists")),
    url(r'^submissions/', include('submissions.urls', namespace="submissions")),
    url(r'^submission/', include('submissions.urls', namespace="_submissions")),
    url(r'^theses/', include('theses.urls', namespace="theses")),
    url(r'^thesis/', include('theses.urls', namespace="_theses")),
    url(r'^meetings/', include('virtualmeetings.urls', namespace="virtualmeetings")),
    url(r'^news/', include('news.urls', namespace="news")),
    url(r'^notifications/', include('notifications.urls', namespace="notifications")),
    url(r'^petitions/', include('petitions.urls', namespace="petitions")),
    url(r'^proceedings/', include('proceedings.urls', namespace="proceedings")),
    url(r'^production/', include('production.urls', namespace="production")),
    url(r'^partners/', include('partners.urls', namespace="partners")),
    url(r'^stats/', include('stats.urls', namespace="stats")),
    # Keep temporarily for historical reasons
    url(r'^supporting_partners/', include('partners.urls', namespace="_partners")),
    url(r'^silk/', include('silk.urls', namespace='silk')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
