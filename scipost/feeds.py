from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse

from scipost.models import NewsItem
from comments.models import Comment

class LatestCommentsFeedRSS(Feed):
    title = "SciPost Latest Comments"
    description = "SciPost Latest Comments"
    link = "/comments/"

    def items(self):
        return Comment.objects.filter(status__gte=0).order_by('-date_submitted')[:5]

    def item_title(self, item):
        return item.comment_text[:50]

    def item_description(self, item):
        return item.description

    def item_link(self, item):
        if item.commentary:
            return reverse('commentaries:commentary', 
                           kwargs={'arxiv_or_DOI_string': item.commentary.arxiv_or_DOI_string})
        elif item.submission:
            return reverse('submissions:submission', 
                           kwargs={'arxiv_identifier_w_vn_nr': 
                                   item.submission.arxiv_identifier_w_vn_nr,})
        elif item.thesislink:
            return reverse('theses:thesis', 
                           kwargs={'thesislink_id': item.thesislink.id})
        else:
            return reverse('scipost:index')

class LatestCommentsFeedAtom(LatestCommentsFeedRSS):
    feed_type = Atom1Feed
    description = LatestCommentsFeedRSS.description



class LatestNewsFeedRSS(Feed):
    title = 'SciPost Latest News'
    link = '/news/'
    description = "SciPost recent news and announcements"

    def items(self):
        return NewsItem.objects.order_by('-date')[:5]

    def item_title(self, item):
        return item.headline

    def item_description(self, item):
        return item.blurb

    def item_link(self, item):
        return item.followup_link


class LatestNewsFeedAtom(LatestNewsFeedRSS):
    feed_type = Atom1Feed
    description = LatestNewsFeedRSS.description



