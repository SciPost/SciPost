__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from journals.models import Publication
from journals.forms import PublicationDynSelForm
from profiles.models import Profile
from profiles.forms import ProfileSelectForm, ProfileDynSelForm
from colleges.forms import FellowshipDynSelForm
from colleges.models import Fellowship
from submissions.models.submission import Submission

from .models import Series, Collection, CollectionPublicationsTable


class SeriesListView(ListView):
    """
    List view for Series.
    """

    model = Series


class SeriesDetailView(DetailView):
    """
    Detail view for a Series.
    """

    model = Series

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Sort collections in series by event start date
        context["collections"] = self.object.collections.all().order_by(
            "event_start_date"
        )
        return context


class CollectionDetailView(DetailView):
    """
    Detail view for a Collection.
    """

    model = Collection

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["expected_author_form"] = ProfileSelectForm()
        context["collection_submissions"] = self.object.submissions.filter(
            status__in=[
                Submission.REFEREEING_IN_PREPARATION,
                Submission.IN_REFEREEING,
                Submission.REFEREEING_CLOSED,
                Submission.AWAITING_RESUBMISSION,
                Submission.VOTING_IN_PREPARATION,
                Submission.IN_VOTING,
                Submission.ACCEPTED_IN_TARGET,
                Submission.ACCEPTED_IN_ALTERNATIVE_AWAITING_PUBOFFER_ACCEPTANCE,
                Submission.ACCEPTED_IN_ALTERNATIVE,
            ]
        )
        return context


@permission_required("scipost.can_manage_series")
def _hx_collection_expected_authors(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    form = ProfileDynSelForm(
        initial={
            "action_url_name": "series:_hx_collection_expected_author_action",
            "action_url_base_kwargs": {"slug": collection.slug, "action": "add"},
            "action_target_element_id": "author_profiles",
            "action_target_swap": "innerHTML",
        }
    )
    context = {"collection": collection, "author_profile_search_form": form}
    return render(request, "series/_hx_collection_expected_authors.html", context)


@permission_required("scipost.can_manage_series")
def _hx_collection_expected_author_action(request, slug, profile_id, action):
    collection = get_object_or_404(Collection, slug=slug)
    profile = get_object_or_404(Profile, pk=profile_id)
    if action == "add":
        collection.expected_authors.add(profile)
    if action == "remove":
        # If this person already has a Publication, abort
        if collection.publications.filter(authors__profile=profile).exists():
            messages.error(
                request, f"{profile} is author of a Publication; removal aborted."
            )
        else:
            collection.expected_authors.remove(profile)
    return redirect(
        reverse(
            "series:_hx_collection_expected_authors", kwargs={"slug": collection.slug}
        )
    )


@permission_required("scipost.can_manage_series")
def _hx_collection_expected_editors(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    form = FellowshipDynSelForm(
        initial={
            "action_url_name": "series:_hx_collection_expected_editor_action",
            "action_url_base_kwargs": {"slug": collection.slug, "action": "add"},
            "action_target_element_id": "editor_fellowships",
            "action_target_swap": "innerHTML",
        }
    )
    context = {"collection": collection, "editor_fellowship_search_form": form}
    return render(request, "series/_hx_collection_expected_editors.html", context)


@permission_required("scipost.can_manage_series")
def _hx_collection_expected_editor_action(request, slug, fellowship_id, action):
    collection = get_object_or_404(Collection, slug=slug)
    fellowship = get_object_or_404(Fellowship, pk=fellowship_id)
    if action == "add":
        collection.expected_editors.add(fellowship)
    if action == "remove":
        collection.expected_editors.remove(fellowship)
    return redirect(
        reverse(
            "series:_hx_collection_expected_editors", kwargs={"slug": collection.slug}
        )
    )


@permission_required("scipost.can_manage_series")
def _hx_collection_publications(request, slug):
    collection = get_object_or_404(Collection, slug=slug)
    form = PublicationDynSelForm(
        initial={
            "action_url_name": "series:_hx_collection_publication_action",
            "action_url_base_kwargs": {"slug": collection.slug, "action": "add"},
            "action_target_element_id": "publications",
        }
    )
    context = {"collection": collection, "publication_search_form": form}
    return render(request, "series/_hx_collection_publications.html", context)


@permission_required("scipost.can_manage_series")
def _hx_collection_publication_action(request, slug, doi_label, action):
    collection = get_object_or_404(Collection, slug=slug)
    publication = get_object_or_404(Publication, doi_label=doi_label)
    if action == "add":
        collection.cleanup_ordering()
        cpt, created = CollectionPublicationsTable.objects.get_or_create(
            collection=collection, publication=publication
        )
        if created:
            messages.success(
                request, f"Added {publication.doi_label} to the Collection."
            )
        else:
            messages.error(request, f"{publication.doi_label} is already listed.")
    if action == "remove":
        CollectionPublicationsTable.objects.filter(
            collection=collection, publication=publication
        ).delete()
        collection.cleanup_ordering()
        # todo: cleanup order
    return redirect(
        reverse("series:_hx_collection_publications", kwargs={"slug": collection.slug})
    )


@permission_required("scipost.can_manage_series")
def _hx_collection_toggle_enforce_expected_authors(request, slug):
    """
    Toggle the enforce_expected_authors flag for a Collection.
    """
    collection = get_object_or_404(Collection, slug=slug)
    collection.enforce_expected_authors = not collection.enforce_expected_authors
    collection.save()
    return render(
        request,
        "series/_hx_collection_toggle_enforce_expected_authors.html",
        {"collection": collection},
    )
