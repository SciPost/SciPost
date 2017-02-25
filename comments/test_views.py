from django.test import TestCase, RequestFactory, Client
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from scipost.factories import ContributorFactory
from theses.factories import ThesisLinkFactory
from submissions.factories import EICassignedSubmissionFactory

from .factories import CommentFactory
from .forms import CommentForm
from .models import Comment
from .views import new_comment

from common.helpers import model_form_data


class TestNewComment(TestCase):
    fixtures = ['groups', 'permissions']

    def test_submitting_comment_on_thesislink_creates_comment_and_redirects(self):
        """ Valid Comment gets saved """

        contributor = ContributorFactory()
        thesislink = ThesisLinkFactory()
        valid_comment_data = model_form_data(CommentFactory.build(), CommentForm)
        target = reverse('comments:new_comment', kwargs={'object_id': thesislink.id, 'type_of_object': 'thesislink'})

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
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
        valid_comment_data = model_form_data(CommentFactory.build(), CommentForm)
        target = reverse(
            'comments:new_comment',
            kwargs={'object_id': submission.id, 'type_of_object': 'submission'},
        )

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
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


    def test_submitting_comment_on_submission_that_is_not_open_for_commenting_should_be_impossible(self):
        contributor = ContributorFactory()
        submission = EICassignedSubmissionFactory()
        submission.open_for_commenting = False
        submission.save()
        valid_comment_data = model_form_data(CommentFactory.build(), CommentForm)
        target = reverse(
            'comments:new_comment',
            kwargs={'object_id': submission.id, 'type_of_object': 'submission'},
        )

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        request.user = contributor.user
        with self.assertRaises(PermissionDenied):
            response = new_comment(request, object_id=submission.id, type_of_object='submission')
