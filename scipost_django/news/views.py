__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from guardian.decorators import permission_required

from .models import NewsCollection, NewsItem, NewsCollectionNewsItemsTable
from .forms import (
    NewsCollectionForm,
    NewsItemForm,
    NewsCollectionNewsItemsTableForm,
    NewsCollectionNewsItemsOrderingFormSet,
)

from scipost.mixins import PermissionsMixin


class NewsManageView(PermissionsMixin, TemplateView):
    """
    General management of News.
    """

    permission_required = "scipost.can_manage_news"
    template_name = "news/news_manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["newscollections"] = NewsCollection.objects.all()
        context["newsitems"] = NewsItem.objects.all()
        context["add_ni_to_nc_form"] = NewsCollectionNewsItemsTableForm()
        return context


class NewsCollectionView(TemplateView):
    """
    NewsCollection, for public consumption online.
    """

    template_name = "news/newscollection_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nc"] = get_object_or_404(
            NewsCollection,
            date__year=self.kwargs["year"],
            date__month=self.kwargs["month"],
            date__day=self.kwargs["day"],
        )
        return context


class NewsCollectionCreateView(PermissionsMixin, CreateView):
    """
    Create a NewsCollection.
    """

    permission_required = "scipost.can_manage_news"
    form_class = NewsCollectionForm
    template_name = "news/newscollection_create.html"
    success_url = reverse_lazy("news:manage")


class NewsCollectionUpdateView(PermissionsMixin, UpdateView):
    """
    Update a NewsCollection.
    """

    permission_required = "scipost.can_manage_news"
    model = NewsCollection
    form_class = NewsCollectionForm
    template_name = "news/newscollection_update.html"
    success_url = reverse_lazy("news:news")


@permission_required("scipost.can_manage_news", raise_exception=True)
def newscollection_update_ordering(request, pk):
    newscollection = get_object_or_404(NewsCollection, pk=pk)
    ni_formset = NewsCollectionNewsItemsOrderingFormSet(
        request.POST or None,
        queryset=newscollection.newscollectionnewsitemstable_set.order_by("order"),
    )
    if ni_formset.is_valid():
        ni_formset.save()
        messages.success(request, "NewsCollection items ordering updated")
        return redirect(newscollection.get_absolute_url())
    context = {
        "ni_formset": ni_formset,
    }
    return render(request, "news/newscollection_update_ordering.html", context)


class NewsCollectionDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a NewsCollection.
    """

    permission_required = "scipost.can_manage_news"
    model = NewsCollection
    success_url = reverse_lazy("news:news")


class NewsItemCreateView(PermissionsMixin, CreateView):
    """
    Create a NewsItem.
    """

    permission_required = "scipost.can_manage_news"
    form_class = NewsItemForm
    template_name = "news/newsitem_create.html"
    success_url = reverse_lazy("news:news")


class NewsItemDetailView(DetailView):
    model = NewsItem


class NewsItemUpdateView(PermissionsMixin, UpdateView):
    """
    Update a NewsItem.
    """

    permission_required = "scipost.can_manage_news"
    model = NewsItem
    form_class = NewsItemForm
    template_name = "news/newsitem_update.html"
    success_url = reverse_lazy("news:news")


class NewsItemDeleteView(PermissionsMixin, DeleteView):
    """
    Delete a NewsItem.
    """

    permission_required = "scipost.can_manage_news"
    model = NewsItem
    success_url = reverse_lazy("news:news")


class NewsCollectionNewsItemsTableCreateView(PermissionsMixin, CreateView):
    """
    Add a NewsItem to a NewsCollection.
    """

    permission_required = "scipost.can_manage_news"
    form_class = NewsCollectionNewsItemsTableForm
    success_url = reverse_lazy("news:manage")

    def form_valid(self, form):
        nc = get_object_or_404(NewsCollection, id=self.kwargs["ncpk"])
        form.instance.newscollection = nc
        form.instance.order = nc.newscollectionnewsitemstable_set.all().count() + 1
        messages.success(self.request, "Successfully added NewsItem to NewsCollection")
        return super().form_valid(form)


class NewsListView(ListView):
    model = NewsItem
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(published=True)
