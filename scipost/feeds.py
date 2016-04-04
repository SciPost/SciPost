from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from comments.models import Comment

class LatestCommentFeed(Feed):
    title = "SciPost Latest Comments"
    link = "/"

    def items(self):
        return Comment.objects.filter(status__gte=0).order_by('-date_submitted')[:5]

    def item_title(self, item):
        return item.comment_text[:50]

#    def item_description(self, item):
#        return item.description

    def item_link(self, item):
        if item.commentary:
            return reverse('commentaries:commentary', kwargs={'arxiv_or_DOI_string': item.commentary.arxiv_or_DOI_string})
        elif item.submission:
            return reverse('submissions:submission', kwargs={'submission_id': item.submission.id})
        elif item.thesislink:
            return reverse('theses:thesis', kwargs={'thesislink_id': item.thesislink.id})
        else:
            return reverse('scipost:index')
