from django.shortcuts import render
from django.views.generic.list import ListView
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Citable
from .forms import CitableSearchForm

class CitableListView(ListView):

    model = Citable
    template_name = 'citable_list.html'
    form = CitableSearchForm
    paginate_by = 10

    def get_queryset(self):
        self.form = self.form(self.request.GET)

        if self.form.is_valid() and self.form.has_changed():
            queryset = self.form.search_results()
        else:
            # queryset = Citable.objects.simple().limit(100)
            queryset = Citable.objects.simple().order_by('-metadata.is-referenced-by-count').limit(10)

        return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Form into the context!
        context['form'] = self.form

        if self.form.is_valid() and self.form.has_changed():
            context['search'] = True
        else:
            context['browse'] = True

        return context

    def get_paginate_by(self, queryset):
        """
        Dynamically compute pagination setting.

        Can be used to disable pagination on 'empty' search -> manually doing .limit(N) seems
        to be much faster with mongoengine than Django's pagination

        Also you can add an extra parameter to specify pagination size, like so:
            return self.request.GET.get('paginate_by', self.paginate_by)
        """
        if self.request.GET:
            return self.paginate_by
        else:
            return None
