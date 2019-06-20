__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'markup'

urlpatterns = [

    url(
        r'^process/$',
        views.process,
        name='process'
    ),
    url(
        r'^help/$',
        views.markup_help,
        name='help'
    ),
    url(
        r'^help/plaintext$',
        views.plaintext_help,
        name='plaintext_help'
    ),
    url(
        r'^help/Markdown$',
        views.markdown_help,
        name='markdown_help'
    ),
    url(
        r'^help/reStructuredText$',
        views.restructuredtext_help,
        name='restructuredtext_help'
    ),
]
