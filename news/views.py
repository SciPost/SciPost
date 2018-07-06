__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import NewsLetter, NewsItem
from .forms import NewsLetterForm, NewsItemForm, NewsLetterNewsItemsTableForm

from scipost.mixins import PermissionsMixin


class NewsManageView(PermissionsMixin, TemplateView):
    """
    General management of News.
    """
    permission_required = 'scipost.can_manage_news'
    template_name = 'news/news_manage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['newsletters'] = NewsLetter.objects.all()
        context['newsitems'] = NewsItem.objects.all()
        context['add_ni_to_nl_form'] = NewsLetterNewsItemsTableForm()
        return context


class NewsLetterView(TemplateView):
    """
    Newsletter, for public consumption online.
    """
    template_name = 'news/newsletter_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nl'] = get_object_or_404(NewsLetter,
                                          date__year=self.kwargs['year'],
                                          date__month=self.kwargs['month'],
                                          date__day=self.kwargs['day'])
        return context


class NewsLetterCreateView(PermissionsMixin, CreateView):
    """
    Create a NewsLetter.
    """
    permission_required = 'scipost.can_manage_news'
    form_class = NewsLetterForm
    template_name = 'news/newsletter_create.html'
    success_url = reverse_lazy('news:manage')


class NewsLetterUpdateView(PermissionsMixin, UpdateView):
    """
    Update a NewsLetter.
    """
    permission_required = 'scipost.can_manage_news'
    model = NewsLetter
    form_class = NewsLetterForm
    template_name = 'news/newsletter_update.html'
    success_url = reverse_lazy('news:news')


class NewsLetterDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a NewsLetter.
    """
    permission_required = 'scipost.can_manage_news'
    model = NewsLetter
    success_url = reverse_lazy('news:news')


class NewsItemCreateView(PermissionsMixin, CreateView):
    """
    Create a NewsItem.
    """
    permission_required = 'scipost.can_manage_news'
    form_class = NewsItemForm
    template_name = 'news/newsitem_create.html'
    success_url = reverse_lazy('news:news')


class NewsItemUpdateView(PermissionsMixin, UpdateView):
    """
    Update a NewsItem.
    """
    permission_required = 'scipost.can_manage_news'
    model = NewsItem
    form_class = NewsItemForm
    template_name = 'news/newsitem_update.html'
    success_url = reverse_lazy('news:news')


class NewsItemDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a NewsItem.
    """
    permission_required = 'scipost.can_manage_news'
    model = NewsItem
    success_url = reverse_lazy('news:news')


class NewsLetterNewsItemsTableCreateView(PermissionsMixin, CreateView):
    """
    Add a NewsItem to a NewsLetter.
    """
    permission_required = 'scipost.can_manage_news'
    form_class = NewsLetterNewsItemsTableForm
    success_url = reverse_lazy('news:manage')

    def form_valid(self, form):
        nl = get_object_or_404(NewsLetter, id=self.kwargs['nlpk'])
        form.instance.newsletter = nl
        form.instance.order = nl.newsletternewsitemstable_set.all().count() + 1
        messages.success(self.request, 'Successfully added News Item to Newsletter')
        return super().form_valid(form)


class NewsListView(ListView):
    model = NewsItem
    paginate_by = 10
