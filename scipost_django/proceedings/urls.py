__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include

from . import views

app_name = 'proceedings'

urlpatterns = [
    # Proceedings
    path(
        '',
        views.proceedings,
        name='proceedings'
    ),
    path(
        'add/',
        views.ProceedingsAddView.as_view(),
        name='proceedings_add'
    ),
    path(
        '<int:id>/', include([
            path(
                '',
                views.proceedings_details,
                name='proceedings_details'
            ),
            path(
                'edit',
                views.ProceedingsUpdateView.as_view(),
                name='proceedings_edit'
            ),
        ])
    ),
]
