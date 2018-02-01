from django.shortcuts import render
from django.views.generic.list import ListView
from django.utils import timezone

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
            queryset = Citable.objects.simple().order_by('-metadata.is-referenced-by-count').limit(100)

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
