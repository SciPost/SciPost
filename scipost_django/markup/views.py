__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .constants import (
    PlainTextSuggestedFormatting,
    PlainTextSnippets,
    MarkdownSuggestedFormatting,
    MarkdownSnippets,
    ReSTSuggestedFormatting,
    ReStructuredTextSnippets,
)
from .forms import MarkupTextForm


@login_required
def process(request):
    """
    API call to process the POSTed text.

    This returns a JSON dict containing

    * language
    * processed_markup
    """
    form = MarkupTextForm(request.POST or None)
    if form.is_valid():
        return JsonResponse(form.get_processed_markup())
    return JsonResponse({})


@login_required
def _hx_process(request, field):
    """
    API call to process the POSTed text in given for field. Returns an HTML snippet.
    """
    if request.method == "POST":
        data = request.POST.copy()
        data["markup_text"] = request.POST.get(field, None)
        form = MarkupTextForm(data)
        if form.is_valid():
            return render(
                request,
                "markup/forms/widgets/_hx_textarea_widget_value_processed.html",
                context={
                    "markup": form.get_processed_markup(),
                },
            )
    return HttpResponse()


def markup_help(request):
    """
    General help page about markup facilities at SciPost.
    """
    context = {
        "PlainTextSuggestions": PlainTextSuggestedFormatting,
        "MarkdownSuggestions": MarkdownSuggestedFormatting,
        "ReSTSuggestions": ReSTSuggestedFormatting,
    }
    return render(request, "markup/help.html", context)


def plaintext_help(request):
    """
    Help page for plain text.
    """
    context = {
        "snippets": PlainTextSnippets,
    }
    return render(request, "markup/plaintext_help.html", context)


def markdown_help(request):
    """
    Help page for Markdown.
    """
    context = {
        "suggestions": MarkdownSuggestedFormatting,
        "snippets": MarkdownSnippets,
    }
    return render(request, "markup/markdown_help.html", context)


def restructuredtext_help(request):
    """
    Help page for reStructuredText.
    """
    context = {
        "snippets": ReStructuredTextSnippets,
    }
    return render(request, "markup/restructuredtext_help.html", context)
