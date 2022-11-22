__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter

from scipost import views as scipost_views
from organizations.views import OrganizationListView

from affiliates.converters import Crossref_DOI_converter
from colleges.converters import CollegeSlugConverter
from comments.converters import CommentDOILabelConverter, AuthorReplyDOILabelConverter
from common.converters import (
    UnicodeSlugConverter,
    FourDigitYearConverter,
    TwoDigitMonthConverter,
    TwoDigitDayConverter,
)
from journals.converters import (
    JournalDOILabelConverter,
    IssueDOILabelConverter,
    PublicationDOILabelConverter,
)
from ontology.converters import AcademicFieldSlugConverter, SpecialtySlugConverter
from submissions.converters import (
    IdentifierWithoutVersionNumberConverter,
    IdentifierConverter,
    ReportDOILabelConverter,
)


######################################
# Register all custom converters here:
######################################

# affiliates
register_converter(Crossref_DOI_converter, "doi")
# colleges
register_converter(CollegeSlugConverter, "college")
# comments
register_converter(CommentDOILabelConverter, "comment_doi_label")
register_converter(AuthorReplyDOILabelConverter, "author_reply_doi_label")
# common
register_converter(UnicodeSlugConverter, "slug")
register_converter(FourDigitYearConverter, "YYYY")
register_converter(TwoDigitMonthConverter, "MM")
register_converter(TwoDigitDayConverter, "DD")
# journals
register_converter(JournalDOILabelConverter, "journal_doi_label")
register_converter(IssueDOILabelConverter, "issue_doi_label")
register_converter(PublicationDOILabelConverter, "publication_doi_label")
# ontology
register_converter(AcademicFieldSlugConverter, "acad_field")
register_converter(SpecialtySlugConverter, "specialty")
# submissions
register_converter(IdentifierWithoutVersionNumberConverter, "identifier_wo_vn_nr")
register_converter(IdentifierConverter, "identifier")
register_converter(ReportDOILabelConverter, "report_doi_label")

######################################
# End of custom converter registration
######################################


# Disable admin login view which is essentially a 2FA workaround.
admin.site.login = login_required(admin.site.login)

# Base URLs
urlpatterns = [
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("sitemap.xml", scipost_views.sitemap_xml, name="sitemap_xml"),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("affiliates/", include("affiliates.urls", namespace="affiliates")),
    path("api/", include("api.urls", namespace="api")),
    path("mail/", include("apimail.urls", namespace="apimail")),
    path(
        "10.21468/<journal_doi_label:doi_label>/",
        include("journals.urls.journal", namespace="prefixed_journal"),
    ),
    path(
        "<journal_doi_label:doi_label>/",
        include("journals.urls.journal", namespace="journal"),
    ),
    path("", include("scipost.urls", namespace="scipost")),
    path("careers/", include("careers.urls", namespace="careers")),
    path("colleges/", include("colleges.urls", namespace="colleges")),
    path("commentaries/", include("commentaries.urls", namespace="commentaries")),
    path("commentary/", include("commentaries.urls", namespace="_commentaries")),
    path("comments/", include("comments.urls", namespace="comments")),
    path("edadmin/", include("edadmin.urls", namespace="edadmin")),
    path("forums/", include("forums.urls", namespace="forums")),
    path("funders/", include("funders.urls", namespace="funders")),
    path("finances/", include("finances.urls", namespace="finances")),
    path("guides/", include("guides.urls", namespace="guides")),
    path("helpdesk/", include("helpdesk.urls", namespace="helpdesk")),
    path("invitations/", include("invitations.urls", namespace="invitations")),
    path("journals/", include("journals.urls.general", namespace="journals")),
    path("mailing_list/", include("mailing_lists.urls", namespace="mailing_lists")),
    path("markup/", include("markup.urls", namespace="markup")),
    path("submissions/", include("submissions.urls", namespace="submissions")),
    path("submission/", include("submissions.urls", namespace="_submissions")),
    path("theses/", include("theses.urls", namespace="theses")),
    path("thesis/", include("theses.urls", namespace="_theses")),
    path("mails/", include("mails.urls", namespace="mails")),
    path("news/", include("news.urls", namespace="news")),
    path("ontology/", include("ontology.urls", namespace="ontology")),
    path("organizations/", include("organizations.urls", namespace="organizations")),
    path("petitions/", include("petitions.urls", namespace="petitions")),
    path("preprints/", include("preprints.urls", namespace="preprints")),
    path("proceedings/", include("proceedings.urls", namespace="proceedings")),
    path("production/", include("production.urls", namespace="production")),
    path("profiles/", include("profiles.urls", namespace="profiles")),
    path("security/", include("security.urls", namespace="security")),
    path("series/", include("series.urls", namespace="series")),
    path("sponsors/", include("sponsors.urls", namespace="sponsors")),
    path("stats/", include("stats.urls", namespace="stats")),
    path("webinars/", include("webinars.urls", namespace="webinars")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
