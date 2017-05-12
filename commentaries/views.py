import re
import requests

from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Q
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.http import Http404

from .models import Commentary
from .forms import RequestCommentaryForm, DOIToQueryForm, IdentifierToQueryForm, VetCommentaryForm, \
    CommentarySearchForm, RequestPublishedArticleForm

from comments.models import Comment
from comments.forms import CommentForm
from scipost.models import Contributor
from scipost.services import ArxivCaller

import strings


################
# Commentaries
################

# class RequestCommentaryMixin(object):
#     def get_context_data(self, **kwargs):
#         '''Pass the DOI and identifier forms to the context.'''
#         if 'request_commentary_form' not in kwargs:
#             # Only intercept if not prefilled
#             kwargs['request_commentary_form'] = RequestCommentaryForm()
#
#         context = super(RequestCommentaryMixin, self).get_context_data(**kwargs)
#
#         context['existing_commentary'] = None
#         context['doiform'] = DOIToQueryForm()
#         context['identifierform'] = IdentifierToQueryForm()
#         return context


# @method_decorator(permission_required(
#     'scipost.can_request_commentary_pages', raise_exception=True), name='dispatch')
# class RequestCommentary(LoginRequiredMixin, RequestCommentaryMixin, CreateView):
#     form_class = RequestCommentaryForm
#     template_name = 'commentaries/request_commentary.html'
#     success_url = reverse_lazy('scipost:personal_page')
#
#     def get_form_kwargs(self, *args, **kwargs):
#         '''User should be included in the arguments to have a valid form.'''
#         form_kwargs = super(RequestCommentary, self).get_form_kwargs(*args, **kwargs)
#         form_kwargs['user'] = self.request.user
#         return form_kwargs
#
#     def form_valid(self, form):
#         form.instance.parse_links_into_urls()
#         messages.success(self.request, strings.acknowledge_request_commentary)
#         return super(RequestCommentary, self).form_valid(form)

@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def request_commentary(request):
    return render(request, 'commentaries/request_commentary.html')

@method_decorator(permission_required(
    'scipost.can_request_commentary_pages', raise_exception=True), name='dispatch')
class RequestPublishedArticle(CreateView):
    form_class = RequestPublishedArticleForm
    template_name = 'commentaries/request_published_article.html'
    success_url = reverse_lazy('scipost:personal_page')

    def get_context_data(self, **kwargs):
        context = super(RequestPublishedArticle, self).get_context_data(**kwargs)
        context['doi_query_form'] = DOIToQueryForm()
        return context


@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def prefill_using_DOI(request):
    if request.method == "POST":
        doi_query_form = DOIToQueryForm(request.POST)
        # The form checks if doi is valid and commentary doesn't already exist.
        if doi_query_form.is_valid():
            prefill_data = doi_query_form.request_published_article_form_prefill_data()
            form = RequestPublishedArticleForm(initial=prefill_data)
        else:
            form = RequestPublishedArticleForm()

        context = {
            'form': form,
            'doi_query_form': doi_query_form,
        }
        return render(request, 'commentaries/request_published_article.html', context)
    else:
        raise Http404

# @permission_required('scipost.can_request_commentary_pages', raise_exception=True)
# def request_published_article(request):
#     if request.method == "POST":
#         doi_form = DOIToQueryForm(request.POST)
#         identifier_form = IdentifierToQueryForm()
#         # The form checks if doi is valid and commentary doesn't already exist.
#         if doi_form.is_valid():
#             doi = doi_form.cleaned_data['doi']
#             crossref_data = DOICaller(doi).data
#             additional_form_data = {'type': 'published', 'pub_DOI': doi}
#             total_form_data = {**crossref_data, **additional_form_data}
#             commentary_form = RequestCommentaryForm(initial=total_form_data)
#             context = {
#                 'request_commentary_form': commentary_form,
#                 'doiform': doi_form,
#                 'identifierform': identifier_form,
#             }
#             return render(request, 'commentaries/request_commentary.html', context)
#         else:
#             context = {
#                 'request_commentary_form': RequestCommentaryForm(),
#                 'doiform': doi_form,
#                 'identifierform': identifier_form
#             }
#             return render(request, 'commentaries/request_commentary.html', context)
#     elif request.method == "GET":
#         context = { 'form': RequestCommentaryForm() }
#         return render(request, 'commentaries/request_published_article.html', context)


@permission_required('scipost.can_request_commentary_pages', raise_exception=True)
def request_arxiv_preprint(request):
    return 1



# def prefill_using_DOI(request):
#     """ Probes CrossRef API with the DOI, to pre-fill the form. """
#     if request.method == "POST":
#         doiform = DOIToQueryForm(request.POST)
#         if doiform.is_valid():
#             # Check if given doi is of expected form:
#             doipattern = re.compile("^10.[0-9]{4,9}/[-._;()/:a-zA-Z0-9]+")
#             errormessage = ''
#             existing_commentary = None
#             if not doipattern.match(doiform.cleaned_data['doi']):
#                 errormessage = 'The DOI you entered is improperly formatted.'
#             elif Commentary.objects.filter(pub_DOI=doiform.cleaned_data['doi']).exists():
#                 errormessage = 'There already exists a Commentary Page on this publication, see'
#                 existing_commentary = get_object_or_404(Commentary,
#                                                         pub_DOI=doiform.cleaned_data['doi'])
#             if errormessage:
#                 form = RequestCommentaryForm()
#                 identifierform = IdentifierToQueryForm()
#                 context = {
#                     'request_commentary_form': form,
#                     'doiform': doiform,
#                     'identifierform': identifierform,
#                     'errormessage': errormessage,
#                     'existing_commentary': existing_commentary}
#                 return render(request, 'commentaries/request_commentary.html', context)
#
#             # Otherwise we query Crossref for the information:
#             try:
#                 queryurl = 'http://api.crossref.org/works/%s' % doiform.cleaned_data['doi']
#                 doiquery = requests.get(queryurl)
#                 doiqueryJSON = doiquery.json()
#                 metadata = doiqueryJSON
#                 pub_title = doiqueryJSON['message']['title'][0]
#                 authorlist = (doiqueryJSON['message']['author'][0]['given'] + ' ' +
#                               doiqueryJSON['message']['author'][0]['family'])
#                 for author in doiqueryJSON['message']['author'][1:]:
#                     authorlist += ', ' + author['given'] + ' ' + author['family']
#                 journal = doiqueryJSON['message']['container-title'][0]
#
#                 try:
#                     volume = doiqueryJSON['message']['volume']
#                 except KeyError:
#                     volume = ''
#
#                 pages = ''
#                 try:
#                     pages = doiqueryJSON['message']['article-number']  # for Phys Rev
#                 except KeyError:
#                     pass
#                 try:
#                     pages = doiqueryJSON['message']['page']
#                 except KeyError:
#                     pass
#
#                 pub_date = ''
#                 try:
#                     pub_date = (str(doiqueryJSON['message']['issued']['date-parts'][0][0]) + '-' +
#                                 str(doiqueryJSON['message']['issued']['date-parts'][0][1]))
#                     try:
#                         pub_date += '-' + str(
#                             doiqueryJSON['message']['issued']['date-parts'][0][2])
#                     except (IndexError, KeyError):
#                         pass
#                 except (IndexError, KeyError):
#                     pass
#                 pub_DOI = doiform.cleaned_data['doi']
#                 form = RequestCommentaryForm(
#                     initial={'type': 'published', 'metadata': metadata,
#                              'pub_title': pub_title, 'author_list': authorlist,
#                              'journal': journal, 'volume': volume,
#                              'pages': pages, 'pub_date': pub_date,
#                              'pub_DOI': pub_DOI})
#                 identifierform = IdentifierToQueryForm()
#                 context = {
#                     'request_commentary_form': form,
#                     'doiform': doiform,
#                     'identifierform': identifierform
#                 }
#                 context['title'] = pub_title
#                 return render(request, 'commentaries/request_commentary.html', context)
#             except (IndexError, KeyError, ValueError):
#                 pass
#         else:
#             pass
#     return redirect(reverse('commentaries:request_commentary'))


# @method_decorator(permission_required(
#     'scipost.can_request_commentary_pages', raise_exception=True), name='dispatch')
# class PrefillUsingIdentifierView(RequestCommentaryMixin, FormView):
#     form_class = IdentifierToQueryForm
#     template_name = 'commentaries/request_commentary.html'
#
#     def form_invalid(self, identifierform):
#         for field, errors in identifierform.errors.items():
#             for error in errors:
#                 messages.warning(self.request, error)
#         return render(self.request, 'commentaries/request_commentary.html',
#                       self.get_context_data(**{}))
#
#     def form_valid(self, identifierform):
#         '''Prefill using the ArxivCaller if the Identifier is valid'''
#         caller = ArxivCaller(Commentary, identifierform.cleaned_data['identifier'])
#         caller.process()
#
#         if caller.is_valid():
#             # Prefill the form
#             metadata = caller.metadata
#             pub_title = metadata['entries'][0]['title']
#             authorlist = metadata['entries'][0]['authors'][0]['name']
#             for author in metadata['entries'][0]['authors'][1:]:
#                 authorlist += ', ' + author['name']
#             arxiv_link = metadata['entries'][0]['id']
#             abstract = metadata['entries'][0]['summary']
#
#             initialdata = {
#                 'type': 'preprint',
#                 'metadata': metadata,
#                 'pub_title': pub_title,
#                 'author_list': authorlist,
#                 'arxiv_identifier': identifierform.cleaned_data['identifier'],
#                 'arxiv_link': arxiv_link,
#                 'pub_abstract': abstract
#             }
#             context = {
#                 'title': pub_title,
#                 'request_commentary_form': RequestCommentaryForm(initial=initialdata)
#             }
#             messages.success(self.request, 'Arxiv completed')
#             return render(self.request, 'commentaries/request_commentary.html',
#                           self.get_context_data(**context))
#         else:
#             msg = caller.get_error_message()
#             messages.error(self.request, msg)
#             return render(self.request, 'commentaries/request_commentary.html',
#                           self.get_context_data(**{}))


@permission_required('scipost.can_vet_commentary_requests', raise_exception=True)
def vet_commentary_requests(request):
    """Show the first commentary thats awaiting vetting"""
    contributor = Contributor.objects.get(user=request.user)
    commentary_to_vet = Commentary.objects.awaiting_vetting().first()  # only handle one at a time
    form = VetCommentaryForm()
    context = {'contributor': contributor, 'commentary_to_vet': commentary_to_vet, 'form': form}
    return render(request, 'commentaries/vet_commentary_requests.html', context)


@permission_required('scipost.can_vet_commentary_requests', raise_exception=True)
def vet_commentary_request_ack(request, commentary_id):
    if request.method == 'POST':
        form = VetCommentaryForm(request.POST, user=request.user, commentary_id=commentary_id)
        if form.is_valid():
            # Get commentary
            commentary = form.get_commentary()
            email_context = {
                'commentary': commentary
            }

            # Retrieve email_template for action
            if form.commentary_is_accepted():
                email_template = 'commentaries/vet_commentary_email_accepted.html'
            elif form.commentary_is_modified():
                email_template = 'commentaries/vet_commentary_email_modified.html'

                request_commentary_form = RequestCommentaryForm(initial={
                    'pub_title': commentary.pub_title,
                    'arxiv_link': commentary.arxiv_link,
                    'pub_DOI_link': commentary.pub_DOI_link,
                    'author_list': commentary.author_list,
                    'pub_date': commentary.pub_date,
                    'pub_abstract': commentary.pub_abstract
                })
            elif form.commentary_is_refused():
                email_template = 'commentaries/vet_commentary_email_rejected.html'
                email_context['refusal_reason'] = form.get_refusal_reason()
                email_context['further_explanation'] = form.cleaned_data['email_response_field']

            # Send email and process form
            email_text = render_to_string(email_template, email_context)
            email_args = (
                'SciPost Commentary Page activated',
                email_text,
                [commentary.requested_by.user.email],
                ['commentaries@scipost.org']
            )
            emailmessage = EmailMessage(*email_args, reply_to=['commentaries@scipost.org'])
            emailmessage.send(fail_silently=False)
            commentary = form.process_commentary()

            # For a modified commentary, redirect to request_commentary_form
            if form.commentary_is_modified():
                context = {'form': request_commentary_form}
                return render(request, 'commentaries/request_commentary.html', context)

    context = {'ack_header': 'SciPost Commentary request vetted.',
               'followup_message': 'Return to the ',
               'followup_link': reverse('commentaries:vet_commentary_requests'),
               'followup_link_label': 'Commentary requests page'}
    return render(request, 'scipost/acknowledgement.html', context)


class CommentaryListView(ListView):
    model = Commentary
    form = CommentarySearchForm
    paginate_by = 10

    def get_queryset(self):
        '''Perform search form here already to get the right pagination numbers.'''
        self.form = self.form(self.request.GET)
        if self.form.is_valid() and self.form.has_changed():
            return self.form.search_results()
        return self.model.objects.vetted().order_by('-latest_activity')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Get newest comments
        context['comment_list'] = (Comment.objects.vetted()
                                   .filter(Q(commentary__isnull=False) |
                                           Q(submission__isnull=False) |
                                           Q(thesislink__isnull=False))
                                   .select_related('author__user', 'submission', 'commentary')
                                   .order_by('-date_submitted')[:10])

        # Form into the context!
        context['form'] = self.form

        # To customize display in the template
        if 'discipline' in self.kwargs:
            context['discipline'] = self.kwargs['discipline']
            context['nrweeksback'] = self.kwargs['nrweeksback']
            context['browse'] = True
        elif not any(self.request.GET[field] for field in self.request.GET):
            context['recent'] = True

        return context


def commentary_detail(request, arxiv_or_DOI_string):
    commentary = get_object_or_404(Commentary, arxiv_or_DOI_string=arxiv_or_DOI_string)
    comments = commentary.comment_set.all()
    form = CommentForm()
    try:
        author_replies = Comment.objects.filter(
            commentary=commentary, is_author_reply=True, status__gte=1)
    except Comment.DoesNotExist:
        author_replies = ()
    context = {'commentary': commentary,
               'comments': comments.filter(status__gte=1).order_by('-date_submitted'),
               'author_replies': author_replies, 'form': form}
    return render(request, 'commentaries/commentary_detail.html', context)
