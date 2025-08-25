__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMessage
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.http import Http404

from ethics.forms import GenAIDisclosureForm

from .models import Commentary
from .forms import (
    DOIToQueryForm,
    ArxivQueryForm,
    VetCommentaryForm,
    RequestCommentaryForm,
    CommentaryListSearchForm,
    RequestPublishedArticleForm,
    RequestArxivPreprintForm,
    CommentSciPostPublication,
)

from comments.models import Comment
from comments.forms import CommentForm
from common.utils import get_current_domain
from journals.models import Publication
from scipost.mixins import PaginationMixin

import strings


@login_required
@permission_required("scipost.can_request_commentary_pages", raise_exception=True)
def request_commentary(request):
    return render(request, "commentaries/request_commentary.html")


@method_decorator(login_required, name="dispatch")
@method_decorator(
    permission_required("scipost.can_request_commentary_pages", raise_exception=True),
    name="dispatch",
)
class RequestCommentary(CreateView):
    success_url = reverse_lazy("scipost:personal_page")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["requested_by"] = self.request.user.contributor
        return kwargs

    def form_valid(self, form):
        messages.success(
            self.request, strings.acknowledge_request_commentary, fail_silently=True
        )
        return super().form_valid(form)


class RequestPublishedArticle(RequestCommentary):
    form_class = RequestPublishedArticleForm
    template_name = "commentaries/request_published_article.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query_form"] = DOIToQueryForm()
        return context


class RequestArxivPreprint(RequestCommentary):
    form_class = RequestArxivPreprintForm
    template_name = "commentaries/request_arxiv_preprint.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query_form"] = ArxivQueryForm()
        return context


@permission_required("scipost.can_request_commentary_pages", raise_exception=True)
def prefill_using_DOI(request):
    if request.method == "POST":
        query_form = DOIToQueryForm(request.POST)
        # The form checks if doi is valid and commentary doesn't already exist.
        if query_form.is_valid():
            prefill_data = query_form.request_published_article_form_prefill_data()
            form = RequestPublishedArticleForm(initial=prefill_data)
            messages.success(request, strings.acknowledge_doi_query, fail_silently=True)
        else:
            form = RequestPublishedArticleForm()

        context = {
            "form": form,
            "query_form": query_form,
        }
        return render(request, "commentaries/request_published_article.html", context)
    else:
        raise Http404


@permission_required("scipost.can_request_commentary_pages", raise_exception=True)
def prefill_using_arxiv_identifier(request):
    if request.method == "POST":
        query_form = ArxivQueryForm(request.POST)
        if query_form.is_valid():
            prefill_data = query_form.request_arxiv_preprint_form_prefill_data()
            form = RequestArxivPreprintForm(initial=prefill_data)
            messages.success(
                request, strings.acknowledge_arxiv_query, fail_silently=True
            )
        else:
            form = RequestArxivPreprintForm()

        context = {
            "form": form,
            "query_form": query_form,
        }
        return render(request, "commentaries/request_arxiv_preprint.html", context)
    else:
        raise Http404


@permission_required("scipost.can_vet_commentary_requests", raise_exception=True)
def vet_commentary_requests(request, commentary_id=None):
    """Show the first commentary thats awaiting vetting"""
    queryset = Commentary.objects.awaiting_vetting().exclude(
        requested_by=request.user.contributor
    )
    if commentary_id:
        # Security fix: Smart asses can vet their own commentary without this line.
        commentary_to_vet = get_object_or_404(queryset, id=commentary_id)
    else:
        commentary_to_vet = queryset.first()

    form = VetCommentaryForm(
        request.POST or None, user=request.user, commentary_id=commentary_id
    )
    if form.is_valid():
        domain = get_current_domain()

        # Get commentary
        commentary = form.get_commentary()
        email_context = {"commentary": commentary, "domain": domain}

        # Retrieve email_template for action
        if form.commentary_is_accepted():
            email_template = "commentaries/vet_commentary_email_accepted.html"
        elif form.commentary_is_refused():
            email_template = "commentaries/vet_commentary_email_rejected.html"
            email_context["refusal_reason"] = form.get_refusal_reason()
            email_context["further_explanation"] = form.cleaned_data[
                "email_response_field"
            ]
        elif form.commentary_is_modified():
            # For a modified commentary, redirect to request_commentary_form
            return redirect(
                reverse("commentaries:modify_commentary_request", args=(commentary.id,))
            )

        # Send email and process form
        email_text = render_to_string(email_template, email_context)
        email_args = (
            "SciPost Commentary Page activated",
            email_text,
            commentary.requested_by.user.email,
            ["commentaries@%s" % domain],
        )
        emailmessage = EmailMessage(*email_args, reply_to=["commentaries@%s" % domain])
        emailmessage.send(fail_silently=False)
        commentary = form.process_commentary()

        messages.success(request, "SciPost Commentary request vetted.")
        return redirect(reverse("commentaries:vet_commentary_requests"))

    context = {"commentary_to_vet": commentary_to_vet, "form": form}
    return render(request, "commentaries/vet_commentary_requests.html", context)


@permission_required("scipost.can_vet_commentary_requests", raise_exception=True)
def modify_commentary_request(request, commentary_id):
    """Modify a commentary request after vetting with status 'modified'."""
    commentary = get_object_or_404(
        (
            Commentary.objects.awaiting_vetting().exclude(
                requested_by=request.user.contributor
            )
        ),
        id=commentary_id,
    )
    form = RequestCommentaryForm(request.POST or None, instance=commentary)
    if form.is_valid():
        domain = get_current_domain()

        # Process commentary data
        commentary = form.save(commit=False)
        commentary.vetted = True
        commentary.save()

        # Send email and process form
        email_template = "commentaries/vet_commentary_email_modified.html"
        email_text = render_to_string(
            email_template, {"commentary": commentary, "domain": domain}
        )
        email_args = (
            "SciPost Commentary Page activated",
            email_text,
            commentary.requested_by.user.email,
            ["commentaries@%s" % domain],
        )
        emailmessage = EmailMessage(*email_args, reply_to=["commentaries@%s" % domain])
        emailmessage.send(fail_silently=False)

        messages.success(request, "SciPost Commentary request modified and vetted.")
        return redirect(reverse("commentaries:vet_commentary_requests"))

    context = {"commentary": commentary, "form": form}
    return render(request, "commentaries/modify_commentary_request.html", context)


class CommentaryListView(PaginationMixin, ListView):
    model = Commentary
    form = CommentaryListSearchForm
    paginate_by = 10
    context_object_name = "commentary_list"

    def get_queryset(self):
        """Perform search form here already to get the right pagination numbers."""
        self.form = self.form(self.request.GET)
        if self.form.is_valid() and self.form.has_changed():
            return self.form.search_results()
        return self.model.objects.vetted().order_by("-latest_activity")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Get newest comments
        context["comment_list"] = Comment.objects.vetted().order_by("-date_submitted")[
            :10
        ]
        # Form into the context!
        context["form"] = self.form
        return context


def commentary_detail(request, arxiv_or_DOI_string):
    commentary = get_object_or_404(
        Commentary.objects.vetted(), arxiv_or_DOI_string=arxiv_or_DOI_string
    )

    form = CommentForm()
    gen_ai_disclosure_form = GenAIDisclosureForm()
    context = {
        "commentary": commentary,
        "form": form,
        "gen_ai_disclosure_form": gen_ai_disclosure_form,
    }
    return render(request, "commentaries/commentary_detail.html", context)


@login_required
@permission_required("scipost.can_submit_comments", raise_exception=True)
@transaction.atomic
def comment_on_publication(request, doi_label):
    """
    This will let authors of an SciPost publication comment on their Publication by
    automatically creating a Commentary page if not exist already.
    """
    publication = get_object_or_404(
        Publication.objects.published(),
        doi_label=doi_label,
        authors=request.user.contributor,
    )
    form = CommentSciPostPublication(
        request.POST or None,
        request.FILES or None,
        publication=publication,
        current_user=request.user,
    )
    gen_ai_disclosure_form = GenAIDisclosureForm(request.POST or None)
    if form.is_valid() and gen_ai_disclosure_form.is_valid():
        comment = form.save()
        gen_ai_disclosure_form.save(
            contributor=request.user.contributor,
            for_object=comment,
        )
        messages.success(request, strings.acknowledge_request_commentary)
        return redirect(comment.content_object.get_absolute_url())
    context = {
        "publication": publication,
        "form": form,
        "gen_ai_disclosure_form": gen_ai_disclosure_form,
    }
    return render(request, "commentaries/comment_on_publication.html", context)
