__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from dal import autocomplete
from guardian.decorators import permission_required

from .models import AcademicField, Specialty, Tag, Topic, RelationAsym
from .forms import SelectTagsForm, SelectLinkedTopicForm, AddRelationAsymForm

from scipost.forms import SearchTextForm
from scipost.mixins import PaginationMixin, PermissionsMixin


def ontology(request):
    context = {
        'select_linked_topic_form': SelectLinkedTopicForm(),
    }
    return render(request, 'ontology/ontology.html', context=context)


class AcademicFieldAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""
    def get_queryset(self):
        qs = AcademicField.objects.all()
        if self.request.GET.get('exclude'):
            qs = qs.exclude(slug=self.request.GET['exclude'])
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('name')


class SpecialtyAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""
    def get_queryset(self):
        qs = Specialty.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by('name')


class TagAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""
    def get_queryset(self):
        qs = Tag.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class TopicAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""
    def get_queryset(self):
        qs = Topic.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class TopicLinkedAutocompleteView(TopicAutocompleteView):
    """To feed the Select2 widget."""
    def get_result_label(self, item):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('ontology:topic_details', kwargs={'slug': item.slug}), item)


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


@permission_required('scipost.can_manage_ontology', return_403=True)
def topic_add_tags(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    select_tags_form = SelectTagsForm(request.POST or None)
    if select_tags_form.is_valid():
        for tag in select_tags_form.cleaned_data['tags']:
            topic.tags.add(tag)
        topic.save()
        messages.success(request, 'Tag(s) %s added to Topic %s' % (
            select_tags_form.cleaned_data['tags'], str(topic)))
    return redirect(reverse('ontology:topic_details', kwargs={'slug': topic.slug}))


@permission_required('scipost.can_manage_ontology', return_403=True)
def topic_remove_tag(request, slug, tag_id):
    topic = get_object_or_404(Topic, slug=slug)
    tag = get_object_or_404(Tag, pk=tag_id)
    topic.tags.remove(tag)
    topic.save()
    return redirect(reverse('ontology:topic_details', kwargs={'slug': topic.slug}))


class TopicListView(PaginationMixin, ListView):
    model = Topic
    paginate_by = 100

    def get_queryset(self):
        """
        Return a queryset of Topics using optional GET data.
        """
        queryset = Topic.objects.all()
        if self.request.GET.get('text'):
            queryset = queryset.filter(name__icontains=self.request.GET['text'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'searchform': SearchTextForm(initial={'text': self.request.GET.get('text')}),
            'select_linked_topic_form': SelectLinkedTopicForm()
        })
        return context


class TopicDetailView(DetailView):
    model = Topic

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['select_tags_form'] = SelectTagsForm()
        context['add_relation_asym_form'] = AddRelationAsymForm(
            initial={'A': self.object, 'B': self.object}
        )
        context['relations_asym'] = RelationAsym.objects.filter(Q(A=self.object) | Q(B=self.object))
        return context


@permission_required('scipost.can_manage_ontology', return_403=True)
def add_relation_asym(request, slug):
    form = AddRelationAsymForm(request.POST or None)
    if form.is_valid():
        relation, created = RelationAsym.objects.get_or_create(
            A=form.cleaned_data['A'], relation=form.cleaned_data['relation'],
            B=form.cleaned_data['B'])
        if created:
            messages.success(request, 'Relation successfully created')
        else:
            messages.info(request, 'This relation already exists')
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse('ontology:topic_details', kwargs={'slug': slug}))


@permission_required('scipost.can_manage_ontology', return_403=True)
def delete_relation_asym(request, relation_id, slug):
    relation = get_object_or_404(RelationAsym, pk=relation_id)
    relation.delete()
    messages.success(request, 'Relation deleted')
    return redirect(reverse('ontology:topic_details', kwargs={'slug': slug}))
