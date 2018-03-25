__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404

from scipost.factories import ContributorFactory
from theses.factories import ThesisLinkFactory
from submissions.factories import EICassignedSubmissionFactory
from commentaries.factories import UnpublishedCommentaryFactory

from .factories import CommentFactory
from .forms import CommentForm
from .models import Comment
from .views import new_comment
from common.helpers import model_form_data
from common.helpers.test import add_groups_and_permissions


class TestNewComment(TestCase):
    def setUp(self):
        add_groups_and_permissions()
        ContributorFactory.create_batch(5)

    def install_messages_middleware(self, request):
        # I don't know what the following three lines do, but they help make a RequestFactory
        # work with the messages middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    def test_submitting_comment_on_thesislink_creates_comment_and_redirects(self):
        """ Valid Comment gets saved """

        contributor = ContributorFactory()
        thesislink = ThesisLinkFactory()
        valid_comment_data = model_form_data(CommentFactory, CommentForm)
        target = reverse('comments:new_comment', kwargs={'object_id': thesislink.id, 'type_of_object': 'thesislink'})

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        self.install_messages_middleware(request)
        request.user = contributor.user
        response = new_comment(request, object_id=thesislink.id, type_of_object='thesislink')

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 1)

        response.client = Client()
        expected_redirect_link = reverse('theses:thesis', kwargs={'thesislink_id': thesislink.id})
        self.assertRedirects(response, expected_redirect_link)

    def test_submitting_comment_on_submission_creates_comment_and_redirects(self):
        contributor = ContributorFactory()
        submission = EICassignedSubmissionFactory()
        submission.open_for_commenting = True
        submission.save()
        valid_comment_data = model_form_data(CommentFactory, CommentForm)
        target = reverse(
            'comments:new_comment',
            kwargs={'object_id': submission.id, 'type_of_object': 'submission'},
        )

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        self.install_messages_middleware(request)
        request.user = contributor.user
        response = new_comment(request, object_id=submission.id, type_of_object='submission')

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 1)

        response.client = Client()
        expected_redirect_link = reverse(
            'submissions:submission',
            kwargs={'arxiv_identifier_w_vn_nr': submission.arxiv_identifier_w_vn_nr}
        )
        self.assertRedirects(response, expected_redirect_link)

    def test_submitting_comment_on_commentary_creates_comment_and_redirects(self):
        """ Valid Comment gets saved """

        contributor = ContributorFactory()
        commentary = UnpublishedCommentaryFactory()
        valid_comment_data = model_form_data(CommentFactory, CommentForm)
        target = reverse('comments:new_comment', kwargs={'object_id': commentary.id, 'type_of_object': 'commentary'})

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        self.install_messages_middleware(request)
        request.user = contributor.user
        response = new_comment(request, object_id=commentary.id, type_of_object='commentary')

        comment_count = commentary.comments.count()
        self.assertEqual(comment_count, 1)

        response.client = Client()
        expected_redirect_link = reverse(
            'commentaries:commentary', kwargs={'arxiv_or_DOI_string': commentary.arxiv_or_DOI_string})
        self.assertRedirects(response, expected_redirect_link)

    def test_submitting_comment_on_submission_that_is_not_open_for_commenting_should_be_impossible(self):
        contributor = ContributorFactory()
        submission = EICassignedSubmissionFactory()
        submission.open_for_commenting = False
        submission.save()
        valid_comment_data = model_form_data(CommentFactory, CommentForm)
        target = reverse(
            'comments:new_comment',
            kwargs={'object_id': submission.id, 'type_of_object': 'submission'},
        )

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        self.install_messages_middleware(request)
        request.user = contributor.user
        with self.assertRaises(Http404):
            new_comment(request, object_id=submission.id, type_of_object='submission')
