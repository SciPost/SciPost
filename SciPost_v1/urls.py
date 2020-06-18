__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

# from rest_framework import routers

from journals.regexes import JOURNAL_DOI_LABEL_REGEX
from scipost import views as scipost_views
from organizations.views import OrganizationListView

# Journal URL Regex
JOURNAL_REGEX = '(?P<doi_label>%s)' % JOURNAL_DOI_LABEL_REGEX


# Disable admin login view which is essentially a 2FA workaround.
admin.site.login = login_required(admin.site.login)

# Base URLs
urlpatterns = [
    url(r'^sitemap.xml$', scipost_views.sitemap_xml, name='sitemap_xml'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('api.urls', namespace='api')),
    path(
        'mail/',
        include('apimail.urls', namespace='apimail')
    ),
    url(r'^10.21468/%s/' % JOURNAL_REGEX,
        include('journals.urls.journal', namespace="prefixed_journal")),
    url(r'^%s/' % JOURNAL_REGEX, include('journals.urls.journal', namespace="journal")),
    url(r'^', include('scipost.urls', namespace="scipost")),
    url(r'^careers/', include('careers.urls', namespace="careers")),
    url(r'^colleges/', include('colleges.urls', namespace="colleges")),
    url(r'^commentaries/', include('commentaries.urls', namespace="commentaries")),
    url(r'^commentary/', include('commentaries.urls', namespace="_commentaries")),
    url(r'^comments/', include('comments.urls', namespace="comments")),
    url(r'^forums/', include('forums.urls', namespace="forums")),
    url(r'^funders/', include('funders.urls', namespace="funders")),
    url(r'^finances/', include('finances.urls', namespace="finances")),
    url(r'^guides/', include('guides.urls', namespace="guides")),
    url(r'^helpdesk/', include('helpdesk.urls', namespace="helpdesk")),
    url(r'^invitations/', include('invitations.urls', namespace="invitations")),
    url(r'^journals/', include('journals.urls.general', namespace="journals")),
    url(r'^mailing_list/', include('mailing_lists.urls', namespace="mailing_lists")),
    url(r'^markup/', include('markup.urls', namespace='markup')),
    url(r'^submissions/', include('submissions.urls', namespace="submissions")),
    url(r'^submission/', include('submissions.urls', namespace="_submissions")),
    url(r'^theses/', include('theses.urls', namespace="theses")),
    url(r'^thesis/', include('theses.urls', namespace="_theses")),
    url(r'^mails/', include('mails.urls', namespace="mails")),
    url(r'^news/', include('news.urls', namespace="news")),
    url(r'^notifications/', include('notifications.urls', namespace="notifications")),
    url(r'^ontology/', include('ontology.urls', namespace="ontology")),
    url(r'^organizations/', include('organizations.urls', namespace="organizations")),
    url(r'^petitions/', include('petitions.urls', namespace="petitions")),
    url(r'^preprints/', include('preprints.urls', namespace="preprints")),
    url(r'^proceedings/', include('proceedings.urls', namespace="proceedings")),
    url(r'^production/', include('production.urls', namespace="production")),
    url(r'^profiles/', include('profiles.urls', namespace="profiles")),
    url(r'^security/', include('security.urls', namespace="security")),
    url(r'^series/', include('series.urls', namespace="series")),
    url(r'^sponsors/', include('sponsors.urls', namespace="sponsors")),
    url(r'^stats/', include('stats.urls', namespace="stats")),
    # Deprecated, keep temporarily for historical reasons
    url(r'^partners/', OrganizationListView.as_view(), name='partners'),
    url(r'^supporting_partners/', OrganizationListView.as_view(), name='partners'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
