__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from . import views

app_name = "comments"

urlpatterns = [
    # Comments
    path("", views.CommentListView.as_view(), name="comments"),
    path(
        "reports/<int:report_id>/reply", views.reply_to_report, name="reply_to_report"
    ),
    path(
        "vet_submitted",
        views.vet_submitted_comments_list,
        name="vet_submitted_comments_list",
    ),
    path(
        "new/<str:type_of_object>/<int:object_id>",
        views.new_comment,
        name="new_comment",
    ),
    path("<int:comment_id>/attachment", views.attachment, name="attachment"),
    path("<int:comment_id>/reply", views.reply_to_comment, name="reply_to_comment"),
    path(
        "<int:comment_id>/vet",
        views.vet_submitted_comment,
        name="vet_submitted_comment",
    ),
]
