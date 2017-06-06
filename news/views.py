from django.views.generic.list import ListView

from .models import NewsItem


class NewsListView(ListView):
    model = NewsItem
    paginate_by = 10
