__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from .models import JobOpening


class JobOpeningCreateView(UserPassesTestMixin, CreateView):
    model = JobOpening
    fields = '__all__'
    success_url = reverse_lazy('careers:jobopenings')

    def test_func(self):
        return self.request.user.has_perm('careers.can_add_jobopening')


class JobOpeningUpdateView(UserPassesTestMixin, UpdateView):
    model = JobOpening
    fields = '__all__'
    success_url = reverse_lazy('careers:jobopenings')

    def test_func(self):
        return self.request.user.has_perm('careers.can_add_jobopening')


class JobOpeningListView(ListView):
    model = JobOpening


class JobOpeningDetailView(DetailView):
    model = JobOpening
