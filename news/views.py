__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.views.generic.list import ListView

from .models import NewsItem


class NewsListView(ListView):
    model = NewsItem
    paginate_by = 10
