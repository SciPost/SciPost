__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from .models import Topic, RelationAsym, RelationSym

from scipost.mixins import PaginationMixin, PermissionsMixin


def ontology(request):
    return render(request, 'ontology/ontology.html')


class TopicCreateView(PermissionsMixin, CreateView):
    """
    Create a new Topic for an Ontology.
    """
    permission_required = 'scipost.can_manage_ontology'
    model = Topic
    fields = '__all__'
    template_name = 'ontology/topic_form.html'
    success_url = reverse_lazy('ontology:topics')


class TopicUpdateView(PermissionsMixin, UpdateView):
    """
    Update a Topic for an Ontology.
    """
    permission_required = 'scipost.can_manage_ontology'
    model = Topic
    fields = '__all__'
    template_name = 'ontology/topic_form.html'
    success_url = reverse_lazy('ontology:topics')


class TopicListView(PaginationMixin, ListView):
    model = Topic
    paginate_by = 25


class TopicDetailView(DetailView):
    model = Topic

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['relations_asym'] = RelationAsym.objects.filter(Q(A=self.object) | Q(B=self.object))
        return context
