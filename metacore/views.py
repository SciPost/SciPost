__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.views.generic.list import ListView

from .models import Citable
from .forms import CitableSearchForm


class CitableListView(ListView):
    model = Citable
    template_name = 'citable_list.html'
    form = CitableSearchForm

    def get_queryset(self):
        self.form = self.form(self.request.GET or None)

        if self.form.is_valid():# and self.form.has_changed():
            qs = self.form.search_results()
        else:
            qs = Citable.objects.simple().limit(10)
        return qs.order_by(self.get_ordering())


    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Form into the context!
        context['form'] = self.form

        return context

    def get_paginate_by(self, queryset):
        """Dynamically compute pagination setting."""
        try:
            return min(int(self.request.GET.get('results', 10)), 100)
        except ValueError:
            return 10

    def get_ordering(self):
        if not self.request.GET.get('orderby'):
            return '-metadata.is-referenced-by-count'
        elif self.request.GET['orderby'] == 'name':
            return '-title'
        elif self.request.GET['orderby'] == 'journal':
            return '-journal'
        return '-metadata.is-referenced-by-count'
