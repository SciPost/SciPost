from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse

from comments.models import Comment

class LatestCommentFeed(Feed):
    title = "SciPost Latest Comments"
    subtitle = "SciPost Latest Comments"
    link = "/"
    feed_type = Atom1Feed

    def items(self):
        return Comment.objects.filter(status__gte=0).order_by('-date_submitted')[:5]

    def item_title(self, item):
        return item.comment_text[:50]

    def item_subtitle(self, item):
        return item.subtitle

    def item_link(self, item):
        if item.commentary:
            return reverse('commentaries:commentary', kwargs={'arxiv_or_DOI_string': item.commentary.arxiv_or_DOI_string})
        elif item.submission:
            return reverse('submissions:submission', 
                           kwargs={'arxiv_identifier': item.submission.arxiv_identifier,
                                   'arxiv_vn_nr': item.submission.arxiv_vn_nr})
        elif item.thesislink:
            return reverse('theses:thesis', kwargs={'thesislink_id': item.thesislink.id})
        else:
            return reverse('scipost:index')
