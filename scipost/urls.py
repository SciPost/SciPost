from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # Info
    url(r'^about$', views.about, name='about'),
    url(r'^description$', views.description, name='description'),
    url(r'^peer_witnessed_refereeing$', views.peer_witnessed_refereeing, name='peer_witnessed_refereeing'),
    # Registration
    url(r'^register$', views.register, name='register'),
    url(r'^thanks_for_registering$', views.thanks_for_registering, name='thanks for registering'),
    url(r'^vet_registration_requests$', views.vet_registration_requests, name='vet_registration_requests'),
    url(r'^vet_registration_request_ack/(?P<contributor_id>[0-9]+)$', views.vet_registration_request_ack, name='vet_registration_request_ack'),
    # Authentication
    url(r'^login$', views.login_view, name='login'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^personal_page$', views.personal_page, name='personal_page'),
    # Journals
    url(r'^journals$', views.journals, name='journals'),
    # Submissions
    url(r'^submit_manuscript$', views.submit_manuscript, name='submit_manuscript'),
    url(r'^submit_manuscript_ack$', views.submit_manuscript_ack, name='submit_manuscript_ack'),
    url(r'^submissions$', views.submissions, name='submissions'),
    url(r'^submission/(?P<submission_id>[0-9]+)/$', views.submission_detail, name='submission'),
    url(r'^process_new_submissions$', views.process_new_submissions, name='process_new_submissions'),
    url(r'^process_new_submission_ack/(?P<submission_id>[0-9]+)$', views.process_new_submission_ack, name='process_new_submission_ack'),
    url(r'^vote_on_submission/(?P<submission_id>[0-9]+)$', views.vote_on_submission, name='vote_on_submission'),
    url(r'^vote_on_submission_ack$', views.vote_on_submission_ack, name='vote_on_submission_ack'),
    # Reports
    url(r'^submit_report/(?P<submission_id>[0-9]+)$', views.submit_report, name='submit_report'),
#    url(r'^submit_report_ack/(?P<submission_id>[0-9]+)$', views.submit_report_ack, name='submit_report_ack'),
    url(r'^submit_report_ack$', views.submit_report_ack, name='submit_report_ack'),
    url(r'^vote_on_report/(?P<report_id>[0-9]+)$', views.vote_on_report, name='vote_on_report'),
    url(r'^vote_on_report_ack$', views.vote_on_report_ack, name='vote_on_report_ack'),
    url(r'^vet_submitted_reports$', views.vet_submitted_reports, name='vet_submitted_reports'),
    url(r'^vet_submitted_report_ack/(?P<report_id>[0-9]+)$', views.vet_submitted_report_ack, name='vet_submitted_report_ack'),
    url(r'^author_reply_to_report/(?P<report_id>[0-9]+)$', views.author_reply_to_report, name='author_reply_to_report'),
    url(r'^vet_author_replies$', views.vet_author_replies, name='vet_author_replies'),
    url(r'^vet_author_reply_ack/(?P<reply_id>[0-9]+)$', views.vet_author_reply_ack, name='vet_author_reply_ack'),
    # Commentaries
    url(r'^request_commentary$', views.request_commentary, name='request_commentary'),
    url(r'^request_commentary_ack$', views.request_commentary_ack, name='request_commentary_ack'),
    url(r'^vet_commentary_requests$', views.vet_commentary_requests, name='vet_commentary_requests'),
    url(r'^vet_commentary_request_ack/(?P<commentary_id>[0-9]+)$', views.vet_commentary_request_ack, name='vet_commentary_request_ack'),
    url(r'^commentaries$', views.commentaries, name='commentaries'),
    url(r'^commentary/(?P<commentary_id>[0-9]+)/$', views.commentary_detail, name='commentary'),
    url(r'^vote_on_commentary/(?P<commentary_id>[0-9]+)$', views.vote_on_commentary, name='vote_on_commentary'),
    url(r'^vote_on_commentary_ack$', views.vote_on_commentary_ack, name='vote_on_commentary_ack'),
    # Comments
    url(r'^comment_submission_ack$', views.comment_submission_ack, name='comment_submission_ack'),
#    url(r'^(?P<commentary_id>[0-9]+)/vote_on_comment/(?P<comment_id>[0-9]+)$', views.vote_on_comment, name='vote_on_comment'),
    url(r'^reply_to_comment/(?P<comment_id>[0-9]+)$', views.reply_to_comment, name='reply_to_comment'),
    url(r'^author_reply_to_comment/(?P<comment_id>[0-9]+)$', views.author_reply_to_comment, name='author_reply_to_comment'),
    url(r'^vet_submitted_comments$', views.vet_submitted_comments, name='vet_submitted_comments'),
    url(r'^vet_submitted_comment_ack/(?P<comment_id>[0-9]+)$', views.vet_submitted_comment_ack, name='vet_submitted_comment_ack'),
    url(r'^vote_on_comment/(?P<comment_id>[0-9]+)$', views.vote_on_comment, name='vote_on_comment'),
    url(r'^vote_on_comment_ack$', views.vote_on_comment_ack, name='vote_on_comment_ack'),
]
