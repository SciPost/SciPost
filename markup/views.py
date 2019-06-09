__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .constants import MathSnippets, PlainTextSnippets,\
    MarkdownSnippets, ReStructuredTextSnippets
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


def markup_help(request):
    """
    General help page about markup facilities at SciPost.
    """
    return render(request, 'markup/help.html')


def plaintext_help(request):
    """
    Help page for plain text.
    """
    context = {
        'math_snippets': MathSnippets,
        'snippets': PlainTextSnippets,
    }
    return render(request, 'markup/plaintext_help.html', context)

def markdown_help(request):
    """
    Help page for Markdown.
    """
    context = {
        'math_snippets': MathSnippets,
        'snippets': MarkdownSnippets,
    }
    return render(request, 'markup/markdown_help.html', context)


def restructuredtext_help(request):
    """
    Help page for reStructuredText.
    """
    context = {
        'math_snippets': MathSnippets,
        'snippets': ReStructuredTextSnippets,
    }
    return render(request, 'markup/restructuredtext_help.html', context)
