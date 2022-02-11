__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from journals import views as journals_views


app_name = "urls.journals"

urlpatterns = [
    # Journal routes
    path("issues", journals_views.IssuesView.as_view(), name="issues"),
    path("recent", journals_views.redirect_to_about, name="recent"),
    path("accepted", journals_views.redirect_to_about, name="accepted"),
    path("authoring", journals_views.authoring, name="authoring"),
    path("refereeing", journals_views.refereeing, name="refereeing"),
    path("about", journals_views.about, name="about"),
    path("metrics/<specialty:specialty>", journals_views.metrics, name="metrics"),
    path("metrics", journals_views.metrics, name="metrics"),
]
