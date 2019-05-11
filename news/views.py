__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from .models import NewsLetter, NewsItem, NewsLetterNewsItemsTable
from .forms import NewsLetterForm, NewsItemForm, NewsLetterNewsItemsTableForm,\
    NewsLetterNewsItemsOrderingFormSet

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


@permission_required('scipost.can_manage_news', raise_exception=True)
def newsletter_update_ordering(request, pk):
    newsletter = get_object_or_404(NewsLetter, pk=pk)
    ni_formset = NewsLetterNewsItemsOrderingFormSet(
        request.POST or None, queryset=newsletter.newsletternewsitemstable_set.order_by('order'))
    if ni_formset.is_valid():
        ni_formset.save()
        messages.success(request, 'Newsletter items ordering updated')
        return redirect(newsletter.get_absolute_url())
    context = {
        'ni_formset': ni_formset,
    }
    return render(request, 'news/newsletter_update_ordering.html', context)


class NewsLetterNewsItemsOrderingUpdateView(PermissionsMixin, UpdateView):
    """
    Update the ordering of News Items within a Newsletter.
    """
    permission_required = 'scipost.can_manage_news'
    model = NewsLetterNewsItemsTable
    fields = ['order']
    template_name = 'news/newsletter_update_ordering.html'
    success_url = reverse_lazy('news:news')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        newsletter = get_object_or_404(NewsLetter, id=self.kwargs['pk'])
        context['ni_formset'] = NewsLetterNewsItemsOrderingFormSet(
            self.request.POST or None,
            queryset=newsletter.newsletternewsitemstable_set.order_by('order'))
        return context

    # def form_valid(self, form):
    #     context = self.get_context_data()
    #     ni_formset = context['ni_formset']
    #     if ni_formset.is_valid():
    #         # self.object = form.save()
    #         # ni_formset.instance = self.object
    #         ni_formset.save()
    #         return redirect(self.success_url)
    #     else:
    #         return self.render_to_response(self.get_context_data(form=form))


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

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(published=True)
