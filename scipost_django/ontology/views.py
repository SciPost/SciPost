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
from django.core.paginator import Paginator

from dal import autocomplete
from guardian.decorators import permission_required

from common.views import HXDynselAutocomplete

from .models import AcademicField, Specialty, Tag, Topic, RelationAsym
from .forms import (
    SessionAcademicFieldForm,
    SessionSpecialtyForm,
    SelectTagsForm,
    TopicForm,
    TopicDynSelForm,
    SelectLinkedTopicForm,
    AddRelationAsymForm,
    TopicSearchForm,
)

from scipost.forms import SearchTextForm
from scipost.mixins import PaginationMixin, PermissionsMixin


def set_session_acad_field(request):
    """Set the Academic Field to be viewed in the current user session."""
    form = SessionAcademicFieldForm(request.GET or None)
    if form.is_valid():
        # Reset the Specialty if the Academic Field has changed
        if (session_acad_field := request.session.get("session_acad_field_slug")) and (
            form.cleaned_data["acad_field_slug"] != session_acad_field
        ):
            request.session["session_specialty_slug"] = ""

        # Set the Academic Field
        request.session["session_acad_field_slug"] = form.cleaned_data[
            "acad_field_slug"
        ]

    try:
        initial = {
            "acad_field_slug": AcademicField.objects.get(
                slug=request.session["session_acad_field_slug"]
            ).slug
        }
    except AcademicField.DoesNotExist:
        initial = {}
    form = SessionAcademicFieldForm(initial=initial)
    response = render(
        request,
        "ontology/session_acad_field_form.html",
        context={"session_acad_field_form": form},
    )
    response["HX-Trigger"] = "session-acad-field-set"
    return response


def _hx_session_specialty_form(request):
    """Serve the session Specialty choice form."""
    context = {
        "session_specialty_form": SessionSpecialtyForm(
            acad_field_slug=request.session.get("session_acad_field_slug", None),
            initial={
                "specialty_slug": request.session.get("session_specialty_slug", None)
            },
        )
    }
    return render(request, "ontology/session_specialty_form.html", context)


def set_session_specialty(request):
    """Set the Specialty to be viewed in the current user session."""
    form = SessionSpecialtyForm(
        request.GET or None,
        acad_field_slug=request.session.get("session_acad_field_slug", ""),
    )
    if form.is_valid():
        if form.cleaned_data["specialty_slug"] == "all":
            request.session["session_specialty_slug"] = ""
        else:
            request.session["session_specialty_slug"] = form.cleaned_data[
                "specialty_slug"
            ]
    try:
        initial = {
            "specialty_slug": Specialty.objects.get(
                slug=request.session["session_specialty_slug"]
            ).slug
        }
    except (KeyError, Specialty.DoesNotExist):
        initial = {}
    form = SessionSpecialtyForm(
        acad_field_slug=request.session["session_acad_field_slug"], initial=initial
    )
    response = render(
        request,
        "ontology/session_specialty_form.html",
        context={"session_specialty_form": form},
    )
    response["HX-Trigger"] = "session-specialty-set"
    return response


def ontology(request):
    context = {
        "select_linked_topic_form": SelectLinkedTopicForm(),
    }
    return render(request, "ontology/ontology.html", context=context)


class AcademicFieldAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""

    def get_queryset(self):
        qs = AcademicField.objects.all()
        if self.request.GET.get("exclude"):
            qs = qs.exclude(slug=self.request.GET["exclude"])
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by("name")


class SpecialtyAutocompleteView(autocomplete.Select2QuerySetView):
    """To feed the Select2 widget."""

    def get_queryset(self):
        qs = Specialty.objects.all()
        if self.request.GET.get("acad_field_id"):
            qs = qs.filter(acad_field__id=self.request.GET["acad_field_id"])
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.order_by("name")


class HXDynselSpecialtyAutocomplete(HXDynselAutocomplete):
    model = Specialty

    def search(self, queryset, q):
        return queryset.filter(name__icontains=q)


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
        specialties = self.forwarded.get("specialties", None)
        if specialties:
            qs = qs.filter(specialties__in=specialties)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


def _hx_topic_dynsel_list(request):
    form = TopicDynSelForm(request.POST or None)
    if form.is_valid():
        topics = form.search_results()
    else:
        topics = Topic.objects.none()
    context = {
        "topics": topics,
        "action_url_name": form.cleaned_data["action_url_name"],
        "action_url_base_kwargs": (
            form.cleaned_data["action_url_base_kwargs"]
            if "action_url_base_kwargs" in form.cleaned_data
            else {}
        ),
        "action_target_element_id": form.cleaned_data["action_target_element_id"],
    }
    return render(request, "ontology/_hx_topic_dynsel_list.html", context)


class HXDynselTopicAutocomplete(HXDynselAutocomplete):
    model = Topic

    def search(self, queryset, q):
        return queryset.filter(name__icontains=q)


class TopicLinkedAutocompleteView(TopicAutocompleteView):
    """To feed the Select2 widget."""

    def get_result_label(self, item):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("ontology:topic_details", kwargs={"slug": item.slug}),
            item,
        )


class TopicCreateView(PermissionsMixin, CreateView):
    """
    Create a new Topic for an Ontology.
    """

    permission_required = "scipost.can_manage_ontology"
    model = Topic
    form_class = TopicForm
    # fields = "__all__"
    # template_name = "ontology/topic_form.html"
    success_url = reverse_lazy("ontology:topics")


class TopicUpdateView(PermissionsMixin, UpdateView):
    """
    Update a Topic for an Ontology.
    """

    permission_required = "scipost.can_manage_ontology"
    model = Topic
    fields = "__all__"
    template_name = "ontology/topic_form.html"
    success_url = reverse_lazy("ontology:topics")


@permission_required("scipost.can_manage_ontology", return_403=True)
def topic_add_tags(request, slug):
    topic = get_object_or_404(Topic, slug=slug)
    select_tags_form = SelectTagsForm(request.POST or None)
    if select_tags_form.is_valid():
        for tag in select_tags_form.cleaned_data["tags"]:
            topic.tags.add(tag)
        topic.save()
        messages.success(
            request,
            "Tag(s) %s added to Topic %s"
            % (select_tags_form.cleaned_data["tags"], str(topic)),
        )
    return redirect(reverse("ontology:topic_details", kwargs={"slug": topic.slug}))


@permission_required("scipost.can_manage_ontology", return_403=True)
def topic_remove_tag(request, slug, tag_id):
    topic = get_object_or_404(Topic, slug=slug)
    tag = get_object_or_404(Tag, pk=tag_id)
    topic.tags.remove(tag)
    topic.save()
    return redirect(reverse("ontology:topic_details", kwargs={"slug": topic.slug}))


class TopicListView(PaginationMixin, ListView):
    model = Topic
    paginate_by = 100

    def get_queryset(self):
        """
        Return a queryset of Topics using optional GET data.
        """
        queryset = Topic.objects.all()
        if self.request.GET.get("text"):
            queryset = queryset.filter(name__icontains=self.request.GET["text"])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "searchform": SearchTextForm(
                    initial={"text": self.request.GET.get("text")}
                ),
                "select_linked_topic_form": SelectLinkedTopicForm(),
            }
        )
        return context


def _hx_topic_table(request):
    form = TopicSearchForm(request.POST or None)
    topics = form.search()
    paginator = Paginator(topics, 16)
    page_nr = request.GET.get("page")
    page_obj = paginator.get_page(page_nr)
    count = paginator.count
    start_index = page_obj.start_index
    context = {
        "count": count,
        "page_obj": page_obj,
        "start_index": start_index,
    }
    return render(request, "ontology/_hx_topic_table.html", context)


def _hx_topic_search_form(request):
    form = TopicSearchForm(request.POST or None)

    return render(request, "ontology/_hx_topic_search_form.html", {"form": form})


class TopicDetailView(DetailView):
    model = Topic

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["select_tags_form"] = SelectTagsForm()
        context["add_relation_asym_form"] = AddRelationAsymForm(
            initial={"A": self.object, "B": self.object}
        )
        context["relations_asym"] = RelationAsym.objects.filter(
            Q(A=self.object) | Q(B=self.object)
        )
        return context


@permission_required("scipost.can_manage_ontology", return_403=True)
def add_relation_asym(request, slug):
    form = AddRelationAsymForm(request.POST or None)
    if form.is_valid():
        relation, created = RelationAsym.objects.get_or_create(
            A=form.cleaned_data["A"],
            relation=form.cleaned_data["relation"],
            B=form.cleaned_data["B"],
        )
        if created:
            messages.success(request, "Relation successfully created")
        else:
            messages.info(request, "This relation already exists")
    else:
        for error_messages in form.errors.values():
            messages.warning(request, *error_messages)
    return redirect(reverse("ontology:topic_details", kwargs={"slug": slug}))


@permission_required("scipost.can_manage_ontology", return_403=True)
def delete_relation_asym(request, relation_id, slug):
    relation = get_object_or_404(RelationAsym, pk=relation_id)
    relation.delete()
    messages.success(request, "Relation deleted")
    return redirect(reverse("ontology:topic_details", kwargs={"slug": slug}))
