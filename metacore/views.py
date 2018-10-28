from django.views.generic.list import ListView

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

            # search_results() returns None when all form fields are empty
            if queryset is not None:
                return queryset

        # If there's no search or the search form is empty:
        # queryset = Citable.objects.simple().limit(100)
        queryset = Citable.objects.simple().order_by('-metadata.is-referenced-by-count').limit(10)
        return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Form into the context!
        context['form'] = self.form

        if self.search_active():
            context['search'] = True
        else:
            context['browse'] = True

        return context

    def search_active(self):
        """
        Helper method to figure out whether there is a search going on,
        meaning that the form is not empty, or not.
        """
        if self.form.is_valid() and self.form.has_changed() and not self.form.is_empty():
            return True
        else:
            return False

    def get_paginate_by(self, queryset):
        """
        Dynamically compute pagination setting.

        Can be used to disable pagination on 'empty' search -> manually doing .limit(N) seems
        to be much faster with mongoengine than Django's pagination

        Also you can add an extra parameter to specify pagination size, like so:
            return self.request.GET.get('paginate_by', self.paginate_by)
        """
        if self.search_active():
            return self.paginate_by
        else:
            return None
