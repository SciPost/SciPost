__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "blog"

urlpatterns = [
    path(
        "",
        views.blog_index,
        name="blog_index",
    ),
    path(
        "_hx_posts",
        views._hx_posts,
        name="_hx_posts",
    ),
    path(
        "post/<YYYY:year>-<MM:month>-<DD:day>/<slug:slug>",
        views.BlogPostDetailView.as_view(),
        name="blogpost_detail",
    ),
]
