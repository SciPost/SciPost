__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from .models import Topic

from scipost.mixins import PermissionsMixin


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


class TopicListView(ListView):
    model = Topic


class TopicDetailView(DetailView):
    model = Topic
