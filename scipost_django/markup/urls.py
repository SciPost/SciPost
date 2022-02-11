__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "markup"

urlpatterns = [
    path("process/", views.process, name="process"),
    path("help/", views.markup_help, name="help"),
    path("help/plaintext", views.plaintext_help, name="plaintext_help"),
    path("help/Markdown", views.markdown_help, name="markdown_help"),
    path(
        "help/reStructuredText",
        views.restructuredtext_help,
        name="restructuredtext_help",
    ),
]
