from django.shortcuts import render

from .models import NewsItem


def news(request):
    newsitems = NewsItem.objects.all().order_by('-date')
    context = {'newsitems': newsitems}
    return render(request, 'scipost/news.html', context)
