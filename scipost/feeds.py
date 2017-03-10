import datetime

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from django.core.urlresolvers import reverse
from django.db.models import Q

from scipost.models import subject_areas_dict
from comments.models import Comment
from journals.models import Publication
from news.models import NewsItem
from submissions.models import Submission, SUBMISSION_STATUS_PUBLICLY_INVISIBLE


class LatestCommentsFeedRSS(Feed):
    title = "SciPost: Latest Comments"
    description = "SciPost: Latest Comments"
    link = "/comments/"

    def items(self):
        return Comment.objects.filter(status__gte=0).order_by('-date_submitted')[:10]

    def item_title(self, item):
        return item.comment_text[:50]

    def item_description(self, item):
        return item.comment_text[:50]

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
        if subject_area != '':
            queryset = Publication.objects.filter(
                Q(subject_area=subject_area) | Q(secondary_areas__contains=[subject_area])
            ).order_by('-publication_date')[:10]
            queryset.subject_area = subject_area
        else:
            queryset = Publication.objects.order_by('-publication_date')[:10]
            queryset.subject_area = None
        return queryset

    def title(self, obj):
        title_text = 'SciPost: Latest Publications'
        if obj.subject_area:
            title_text += ' in %s' % subject_areas_dict[obj.subject_area]
        return title_text

    def description(self, obj):
        desc = 'SciPost: most recent publications'
        try:
            if obj.subject_area:
                desc += ' in %s' % subject_areas_dict[obj.subject_area]
        except KeyError:
            pass
        return desc

    def items(self, obj):
        return obj

    def item_link(self, item):
        return reverse('scipost:publication_detail',
                       kwargs={'doi_string': item.doi_string})


class LatestPublicationsFeedAtom(LatestPublicationsFeedRSS):
    feed_type = Atom1Feed
    subtitle = LatestPublicationsFeedRSS.description

    def author_name(self):
        return 'SciPost'

    def item_updateddate(self, item):
        return datetime.datetime(item.publication_date.year,
                                 item.publication_date.month,
                                 item.publication_date.day)
