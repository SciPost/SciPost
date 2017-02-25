from django.test import TestCase, RequestFactory, Client
from django.urls import reverse, reverse_lazy
from django.contrib.auth.models import Group

from scipost.factories import ContributorFactory
from theses.factories import ThesisLinkFactory

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
        target = reverse('theses:thesis', kwargs={'thesislink_id': thesislink.id})

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 0)

        request = RequestFactory().post(target, valid_comment_data)
        request.user = contributor.user
        response = new_comment(request, object_id=thesislink.id, type_of_object='thesislink')

        comment_count = Comment.objects.filter(author=contributor).count()
        self.assertEqual(comment_count, 1)

        response.client = Client()
        self.assertRedirects(response, reverse('theses:thesis', kwargs={"thesislink_id":thesislink.id}))
