__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.syndication.views import Feed
from django.http import Http404
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse
from django.db.models import Q

from comments.models import Comment
from commentaries.models import Commentary
from journals.models import Publication
from news.models import NewsItem
from scipost.models import subject_areas_dict
from submissions.constants import SUBMISSION_STATUS_PUBLICLY_INVISIBLE
from submissions.models import Submission
from theses.models import ThesisLink


class LatestCommentsFeedRSS(Feed):
    title = "SciPost: Latest Comments"
    description = "SciPost: Latest Comments"
    link = "/comments/"

    def items(self):
        return Comment.objects.vetted().order_by('-date_submitted')[:10]

    def item_title(self, item):
        return item.comment_text[:50]

    def item_description(self, item):
        return item.comment_text[:50]

    def item_link(self, item):
        if isinstance(item.content_object, Commentary):
            return reverse('commentaries:commentary',
                           kwargs={'arxiv_or_DOI_string': item.content_object.arxiv_or_DOI_string})
        elif isinstance(item.content_object, Submission):
            return reverse('submissions:submission',
                           kwargs={'arxiv_identifier_w_vn_nr':
                                   item.content_object.arxiv_identifier_w_vn_nr})
        elif isinstance(item.content_object, ThesisLink):
            return reverse('theses:thesis',
                           kwargs={'thesislink_id': item.thesislink.id})
        else:
            return reverse('scipost:index')


class LatestCommentsFeedAtom(LatestCommentsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LatestCommentsFeedRSS.description

    def author_name(self):
        return 'SciPost'

    def item_updateddate(self, item):
        return item.date_submitted


class LatestNewsFeedRSS(Feed):
    title = 'SciPost: Latest News'
    link = '/news/'
    description = "SciPost: recent news and announcements"

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
    subtitle = LatestNewsFeedRSS.description

    def author_name(self):
        return 'SciPost'

    def item_updateddate(self, item):
        return datetime.datetime(item.date.year, item.date.month, item.date.day)


class LatestSubmissionsFeedRSS(Feed):
    title_template = 'feeds/latest_submissions_title.html'
    description_template = 'feeds/latest_submissions_description.html'
    link = "/submissions/"

    def get_object(self, request, subject_area=''):
        if subject_area != '':
            queryset = Submission.objects.filter(
                Q(subject_area=subject_area) | Q(secondary_areas__contains=[subject_area])
            ).exclude(status__in=SUBMISSION_STATUS_PUBLICLY_INVISIBLE
            ).order_by('-submission_date')[:10]
            queryset.subject_area = subject_area
        else:
            queryset = Submission.objects.exclude(status__in=SUBMISSION_STATUS_PUBLICLY_INVISIBLE
            ).order_by('-submission_date')[:10]
            queryset.subject_area = None
        return queryset

    def title(self, obj):
        title_text = 'SciPost: Latest Submissions'
        if obj.subject_area:
            title_text += ' in %s' % subject_areas_dict[obj.subject_area]
        return title_text

    def description(self, obj):
        desc = 'SciPost: most recent submissions'
        try:
            if obj.subject_area:
                desc += ' in %s' % subject_areas_dict[obj.subject_area]
        except KeyError:
            pass
        return desc

    def items(self, obj):
        return obj

    def item_link(self, item):
        return reverse('submissions:submission',
                       kwargs={'arxiv_identifier_w_vn_nr': item.arxiv_identifier_w_vn_nr})


class LatestSubmissionsFeedAtom(LatestSubmissionsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LatestSubmissionsFeedRSS.description

    def author_name(self):
        return 'SciPost'

    def item_updateddate(self, item):
        return datetime.datetime(item.submission_date.year,
                                 item.submission_date.month,
                                 item.submission_date.day)


class LatestPublicationsFeedRSS(Feed):
    title_template = 'feeds/latest_publications_title.html'
    description_template = 'feeds/latest_publications_description.html'
    link = "/journals/"

    def get_object(self, request, subject_area=''):
        if subject_area and subject_area not in subject_areas_dict:
            raise Http404('Invalid subject area')
        qs = Publication.objects.published()
        if subject_area:
            qs = qs.filter(
                Q(subject_area=subject_area) | Q(secondary_areas__contains=[subject_area]))
        self.subject_area = subject_area
        return qs.order_by('-publication_date')[:10]

    def title(self, obj):
        title_text = 'SciPost: Latest Publications'
        if self.subject_area:
            title_text += ' in %s' % subject_areas_dict.get(self.subject_area)
        return title_text

    def description(self, obj):
        desc = 'SciPost: most recent publications'
        try:
            if self.subject_area:
                desc += ' in %s' % subject_areas_dict.get(self.subject_area)
        except KeyError:
            pass
        return desc

    def items(self, obj):
        return obj

    def item_link(self, item):
        return item.get_absolute_url()


class LatestPublicationsFeedAtom(LatestPublicationsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LatestPublicationsFeedRSS.description

    def author_name(self):
        return 'SciPost'

    def item_updateddate(self, item):
        return datetime.datetime(item.publication_date.year,
                                 item.publication_date.month,
                                 item.publication_date.day)
