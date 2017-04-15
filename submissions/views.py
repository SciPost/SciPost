import datetime
import feedparser

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Template, Context
from django.utils import timezone

from guardian.decorators import permission_required_or_403
from guardian.mixins import PermissionRequiredMixin
from guardian.shortcuts import assign_perm

from .constants import SUBMISSION_STATUS_VOTING_DEPRECATED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE, SUBMISSION_STATUS, ED_COMM_CHOICES
from .models import Submission, EICRecommendation, EditorialAssignment,\
                    RefereeInvitation, Report, EditorialCommunication
from .forms import SubmissionIdentifierForm, SubmissionForm, SubmissionSearchForm,\
                   RecommendationVoteForm, ConsiderAssignmentForm, AssignSubmissionForm,\
                   SetRefereeingDeadlineForm, RefereeSelectForm, RefereeRecruitmentForm,\
                   ConsiderRefereeInvitationForm, EditorialCommunicationForm,\
                   EICRecommendationForm, ReportForm, VetReportForm, VotingEligibilityForm
from .utils import SubmissionUtils

from comments.models import Comment
from scipost.forms import ModifyPersonalMessageForm, RemarkForm
from scipost.models import Contributor, Remark, RegistrationInvitation

from scipost.services import ArxivCaller
from scipost.utils import Utils
from strings import arxiv_caller_errormessages_submissions

from comments.forms import CommentForm

from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView


###############
# SUBMISSIONS:
###############

class PrefillUsingIdentifierView(PermissionRequiredMixin, FormView):
    form_class = SubmissionIdentifierForm
    template_name = 'submissions/prefill_using_identifier.html'
    permission_required = 'scipost.can_submit_manuscript'
    raise_exception = True

    def post(self, request):
        identifierform = SubmissionIdentifierForm(request.POST)
        if identifierform.is_valid():
            # Use the ArxivCaller class to make the API calls
            caller = ArxivCaller(Submission, identifierform.cleaned_data['identifier'])
            caller.process()

            if caller.is_valid():
                # Arxiv response is valid and can be shown

                metadata = caller.metadata
                is_resubmission = caller.resubmission
                title = metadata['entries'][0]['title']
                authorlist = metadata['entries'][0]['authors'][0]['name']
                for author in metadata['entries'][0]['authors'][1:]:
                    authorlist += ', ' + author['name']
                arxiv_link = metadata['entries'][0]['id']
                abstract = metadata['entries'][0]['summary']
                initialdata = {'is_resubmission': is_resubmission,
                               'metadata': metadata,
                               'title': title, 'author_list': authorlist,
                               'arxiv_identifier_w_vn_nr': caller.identifier_with_vn_nr,
                               'arxiv_identifier_wo_vn_nr': caller.identifier_without_vn_nr,
                               'arxiv_vn_nr': caller.version_nr,
                               'arxiv_link': arxiv_link, 'abstract': abstract}
                if is_resubmission:
                    previous_submissions = caller.previous_submissions
                    resubmessage = ('There already exists a preprint with this arXiv identifier '
                                    'but a different version number. \nYour Submission will be '
                                    'handled as a resubmission.')
                    initialdata['submitted_to_journal'] = previous_submissions[0].submitted_to_journal
                    initialdata['submission_type'] = previous_submissions[0].submission_type
                    initialdata['discipline'] = previous_submissions[0].discipline
                    initialdata['domain'] = previous_submissions[0].domain
                    initialdata['subject_area'] = previous_submissions[0].subject_area
                    initialdata['secondary_areas'] = previous_submissions[0].secondary_areas
                    initialdata['referees_suggested'] = previous_submissions[0].referees_suggested
                    initialdata['referees_flagged'] = previous_submissions[0].referees_flagged
                else:
                    resubmessage = ''

                form = SubmissionForm(initial=initialdata)
                context = {'identifierform': identifierform,
                           'form': form,
                           'resubmessage': resubmessage}
                return render(request, 'submissions/new_submission.html', context)

            else:
                msg = caller.get_error_message(arxiv_caller_errormessages_submissions)
                identifierform.add_error(None, msg)
                return render(request, 'submissions/prefill_using_identifier.html',
                              {'form': identifierform})
        else:
            return render(request, 'submissions/prefill_using_identifier.html',
                          {'form': identifierform})


class SubmissionCreateView(PermissionRequiredMixin, CreateView):
    model = Submission
    fields = [
        'is_resubmission',
        'discipline',
        'submitted_to_journal',
        'submission_type',
        'domain',
        'subject_area',
        'secondary_areas',
        'title',
        'author_list',
        'abstract',
        'arxiv_identifier_w_vn_nr',
        'arxiv_identifier_wo_vn_nr',
        'arxiv_vn_nr',
        'arxiv_link',
        'metadata',
        'author_comments',
        'list_of_changes',
        'remarks_for_editors',
        'referees_suggested',
        'referees_flagged'
    ]

    template_name = 'submissions/new_submission.html'
    permission_required = 'scipost.can_submit_manuscript'
    # Required to use Guardian's CBV PermissionRequiredMixin with a CreateView
    # (see https://github.com/django-guardian/django-guardian/pull/433)
    permission_object = None
    raise_exception = True

    def get(self, request):
        # Only use prefilled forms
        return redirect('submissions:prefill_using_identifier')

    @transaction.atomic
    def form_valid(self, form):
        submitted_by = Contributor.objects.get(user=self.request.user)
        form.instance.submitted_by = submitted_by

        # Save all the information contained in the form
        submission = form.save()

        # Perform all extra actions and set information not contained in the form
        submission.finish_submission()

        if submission.is_resubmission:
            # Assign permissions
            assign_perm('can_take_editorial_actions', submission.editor_in_charge.user, submission)
            ed_admins = Group.objects.get(name='Editorial Administrators')
            assign_perm('can_take_editorial_actions', ed_admins, submission)

            # Assign editor
            assignment = EditorialAssignment(
                submission=submission,
                to=submission.editor_in_charge,
                accepted=True,
                date_created=timezone.now(),
                date_answered=timezone.now(),
            )
            assignment.save()

            # Send emails
            SubmissionUtils.load({'submission': submission})
            SubmissionUtils.send_authors_resubmission_ack_email()
            SubmissionUtils.send_EIC_reappointment_email()
        else:
            # Send emails
            SubmissionUtils.load({'submission': submission})
            SubmissionUtils.send_authors_submission_ack_email()

        context = {'ack_header': 'Thank you for your Submission to SciPost',
                   'ack_message': 'Your Submission will soon be handled by an Editor. ',
                   'followup_message': 'Return to your ',
                   'followup_link': reverse('scipost:personal_page'),
                   'followup_link_label': 'personal page'}
        return render(self.request, 'scipost/acknowledgement.html', context)

    def mark_previous_submissions_as_deprecated(self, previous_submissions):
        for sub in previous_submissions:
            sub.is_current = False
            sub.open_for_reporting = False
            sub.status = 'resubmitted'
            sub.save()

    def previous_submissions(self, form):
        return Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=form.cleaned_data['arxiv_identifier_wo_vn_nr']
        )


class SubmissionListView(ListView):
    model = Submission
    template_name = 'submissions/submissions.html'
    form = SubmissionSearchForm()
    submission_search_list = []
    paginate_by = 10

    def get_queryset(self):
        queryset = Submission.objects.public_overcomplete().filter(is_current=True)
        if 'to_journal' in self.kwargs:
            queryset = queryset.filter(
                latest_activity__gte=timezone.now() + datetime.timedelta(days=-60),
                submitted_to_journal=self.kwargs['to_journal']
            )
        elif 'discipline' in self.kwargs and 'nrweeksback' in self.kwargs:
            discipline = self.kwargs['discipline']
            nrweeksback = self.kwargs['nrweeksback']
            queryset = queryset.filter(
                discipline=discipline,
                latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback))
            )
        elif 'Submit' in self.request.GET:
            queryset = queryset.filter(
                title__icontains=self.request.GET.get('title_keyword', ''),
                author_list__icontains=self.request.GET.get('author', ''),
                abstract__icontains=self.request.GET.get('abstract_keyword', '')
            )

        return queryset.order_by('-submission_date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SubmissionListView, self).get_context_data(**kwargs)

        # Keep any search fields previously filled
        initialdata = {
            'author': self.request.GET.get('author', ''),
            'title_keyword': self.request.GET.get('title_keyword', ''),
            'abstract_keyword': self.request.GET.get('abstract_keyword', '')
        }
        context['form'] = SubmissionSearchForm(initial=initialdata)

        # To customize display in the template
        if 'to_journal' in self.kwargs:
            context['to_journal'] = self.kwargs['to_journal']
        if 'discipline' in self.kwargs:
            context['discipline'] = self.kwargs['discipline']
            context['nrweeksback'] = self.kwargs['nrweeksback']
            context['browse'] = True
        elif 'Submit' not in self.request.GET:
            context['recent'] = True

        return context


def submission_detail_wo_vn_nr(request, arxiv_identifier_wo_vn_nr):
    submission = get_object_or_404(Submission, arxiv_identifier_wo_vn_nr=arxiv_identifier_wo_vn_nr,
                                   is_current=True)
    return(submission_detail(request, submission.arxiv_identifier_w_vn_nr))


def submission_detail(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission, arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    try:
        is_author = request.user.contributor in submission.authors.all()
    except AttributeError:
        is_author = False
    if (submission.status in SUBMISSION_STATUS_PUBLICLY_INVISIBLE
            and not request.user.groups.filter(name__in=['SciPost Administrators',
                                                         'Editorial Administrators',
                                                         'Editorial College']).exists()
            and not is_author):
        raise Http404
    other_versions = Submission.objects.filter(
        arxiv_identifier_wo_vn_nr=submission.arxiv_identifier_wo_vn_nr
    ).exclude(pk=submission.id)

    form = CommentForm()

    reports = submission.reports.all()
    try:
        author_replies = Comment.objects.filter(submission=submission,
                                                is_author_reply=True,
                                                status__gte=1)
    except Comment.DoesNotExist:
        author_replies = ()
    # To check in template whether the user can submit a report:
    try:
        is_author = request.user.contributor in submission.authors.all()
        is_author_unchecked = (not is_author and not
                               (request.user.contributor in submission.authors_false_claims.all()) and
                               (request.user.last_name in submission.author_list))
    except AttributeError:
        is_author = False
        is_author_unchecked = False
    try:
        recommendation = (EICRecommendation.objects.filter_for_user(request.user)
                          .get(submission=submission))
    except (EICRecommendation.DoesNotExist, AttributeError):
        recommendation = None
    comments = submission.comments.all()
    context = {'submission': submission,
               'other_versions': other_versions,
               'recommendation': recommendation,
               'comments': (comments.filter(status__gte=1, is_author_reply=False)
                            .order_by('-date_submitted')),
               'invited_reports': reports.filter(status__gte=1, invited=True),
               'contributed_reports': reports.filter(status__gte=1, invited=False),
               'author_replies': author_replies, 'form': form,
               'is_author': is_author, 'is_author_unchecked': is_author_unchecked}
    return render(request, 'submissions/submission_detail.html', context)


######################
# Editorial workflow #
######################

@login_required
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def editorial_workflow(request):
    """
    Summary page for Editorial Fellows, containing a digest
    of the actions to take to handle Submissions.
    """
    return render(request, 'submissions/editorial_workflow.html')


@login_required
@permission_required('scipost.can_view_pool', raise_exception=True)
def pool(request):
    """
    The Submissions pool contains all submissions which are undergoing
    the editorial process, from submission
    to publication acceptance or rejection.
    All members of the Editorial College have access.
    """
    submissions_in_pool = (Submission.objects.get_pool(request.user)
                           .prefetch_related('referee_invitations', 'remark_set', 'comments'))
    recommendations_undergoing_voting = (EICRecommendation.objects
                                         .get_for_user_in_pool(request.user)
                                         .filter(submission__status__in=['put_to_EC_voting']))
    recommendations_to_prepare_for_voting = (EICRecommendation.objects
                                             .get_for_user_in_pool(request.user)
                                             .filter(submission__status__in=
                                                     ['voting_in_preparation']))
    contributor = Contributor.objects.get(user=request.user)
    assignments_to_consider = EditorialAssignment.objects.filter(
        to=contributor, accepted=None, deprecated=False)
    consider_assignment_form = ConsiderAssignmentForm()
    recs_to_vote_on = (EICRecommendation.objects.get_for_user_in_pool(request.user)
                       .filter(eligible_to_vote=contributor)
                       .exclude(recommendation__in=[-1, -2])
                       .exclude(voted_for=contributor)
                       .exclude(voted_against=contributor)
                       .exclude(voted_abstain=contributor)
                       .exclude(submission__status__in=SUBMISSION_STATUS_VOTING_DEPRECATED))
    rec_vote_form = RecommendationVoteForm()
    remark_form = RemarkForm()
    context = {'submissions_in_pool': submissions_in_pool,
               'submission_status': SUBMISSION_STATUS,
               'recommendations_undergoing_voting': recommendations_undergoing_voting,
               'recommendations_to_prepare_for_voting': recommendations_to_prepare_for_voting,
               'assignments_to_consider': assignments_to_consider,
               'consider_assignment_form': consider_assignment_form,
               'recs_to_vote_on': recs_to_vote_on,
               'rec_vote_form': rec_vote_form,
               'remark_form': remark_form, }
    return render(request, 'submissions/pool.html', context)


@login_required
@permission_required('scipost.can_view_pool', raise_exception=True)
def submissions_by_status(request, status):
    status_dict = dict(SUBMISSION_STATUS)
    if status not in status_dict.keys():
        errormessage = 'Unknown status.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    submissions_of_status = (Submission.objects.get_pool(request.user)
                             .filter(status=status).order_by('-submission_date'))

    context = {
        'submissions_of_status': submissions_of_status,
        'status': status_dict[status],
        'remark_form': RemarkForm()
    }
    return render(request, 'submissions/submissions_by_status.html', context)


@login_required
@permission_required('scipost.can_view_pool', raise_exception=True)
def add_remark(request, arxiv_identifier_w_vn_nr):
    """
    With this method, an Editorial Fellow or Board Member
    is adding a remark on a Submission.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)

    remark_form = RemarkForm(request.POST or None)
    if remark_form.is_valid():
        remark = Remark(contributor=request.user.contributor,
                        submission=submission,
                        date=timezone.now(),
                        remark=remark_form.cleaned_data['remark'])
        remark.save()
        messages.success(request, 'Your remark has succesfully been posted')
    else:
        messages.warning(request, 'The form was invalidly filled.')
    return redirect(reverse('submissions:pool'))


@login_required
@permission_required('scipost.can_assign_submissions', raise_exception=True)
def assign_submission(request, arxiv_identifier_w_vn_nr):
    submission_to_assign = get_object_or_404(Submission.objects.get_pool(request.user),
                                             arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    form = AssignSubmissionForm(discipline=submission_to_assign.discipline)
    context = {'submission_to_assign': submission_to_assign,
               'form': form}
    return render(request, 'submissions/assign_submission.html', context)


@login_required
@permission_required('scipost.can_assign_submissions', raise_exception=True)
def assign_submission_ack(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if request.method == 'POST':
        form = AssignSubmissionForm(request.POST, discipline=submission.discipline)
        if form.is_valid():
            suggested_editor_in_charge = form.cleaned_data['editor_in_charge']
            # TODO: check for possible co-authorships, disqualifying this suggested EIC
            if not suggested_editor_in_charge.is_currently_available():
                errormessage = ('This Fellow is marked as currently unavailable. '
                                'Please go back and select another one.')
                return render(request, 'scipost/error.html', {'errormessage': errormessage})
            ed_assignment = EditorialAssignment(submission=submission,
                                                to=suggested_editor_in_charge,
                                                date_created=timezone.now())
            ed_assignment.save()
            SubmissionUtils.load({'assignment': ed_assignment})
            SubmissionUtils.send_assignment_request_email()

    context = {'ack_header': 'Your assignment request has been sent successfully.',
               'followup_message': 'Return to the ',
               'followup_link': reverse('submissions:pool'),
               'followup_link_label': 'Submissions pool'}
    return render(request, 'scipost/acknowledgement.html', context)


@login_required
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
@transaction.atomic
def accept_or_decline_assignment_ack(request, assignment_id):
    contributor = Contributor.objects.get(user=request.user)
    assignment = get_object_or_404(EditorialAssignment, pk=assignment_id)
    errormessage = None
    if assignment.submission.status == 'assignment_failed':
        errormessage = 'This Submission has failed pre-screening and has been rejected.'
        context = {'errormessage': errormessage}
        return render(request, 'submissions/accept_or_decline_assignment_ack.html', context)
    if assignment.submission.editor_in_charge:
        errormessage = (assignment.submission.editor_in_charge.get_title_display() + ' ' +
                        assignment.submission.editor_in_charge.user.last_name +
                        ' has already agreed to be Editor-in-charge of this Submission.')
        context = {'errormessage': errormessage}
        return render(request, 'submissions/accept_or_decline_assignment_ack.html', context)
    if request.method == 'POST':
        form = ConsiderAssignmentForm(request.POST)
        if form.is_valid():
            assignment.date_answered = timezone.now()
            if form.cleaned_data['accept'] == 'True':
                assignment.accepted = True
                assignment.to = contributor
                assignment.submission.status = 'EICassigned'
                assignment.submission.editor_in_charge = contributor
                assignment.submission.open_for_reporting = True
                deadline = timezone.now() + datetime.timedelta(days=28)  # for papers
                if assignment.submission.submitted_to_journal == 'SciPost Physics Lecture Notes':
                    deadline += datetime.timedelta(days=28)
                assignment.submission.reporting_deadline = deadline
                assignment.submission.open_for_commenting = True
                assignment.submission.latest_activity = timezone.now()

                SubmissionUtils.load({'assignment': assignment})
                SubmissionUtils.deprecate_other_assignments()
                assign_perm('can_take_editorial_actions', contributor.user, assignment.submission)
                ed_admins = Group.objects.get(name='Editorial Administrators')
                assign_perm('can_take_editorial_actions', ed_admins, assignment.submission)
                SubmissionUtils.send_EIC_appointment_email()
                SubmissionUtils.send_author_prescreening_passed_email()
            else:
                assignment.accepted = False
                assignment.refusal_reason = form.cleaned_data['refusal_reason']
                assignment.submission.status = 'unassigned'
            assignment.save()
            assignment.submission.save()

    context = {'assignment': assignment}
    return render(request, 'submissions/accept_or_decline_assignment_ack.html', context)


@login_required
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
@transaction.atomic
def volunteer_as_EIC(request, arxiv_identifier_w_vn_nr):
    """
    Called when a Fellow volunteers while perusing the submissions pool.
    This is an adapted version of the accept_or_decline_assignment_ack method.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    errormessage = None
    if submission.status == 'assignment_failed':
        errormessage = '<h3>Thank you for considering.</h3>'
        errormessage += 'This Submission has failed pre-screening and has been rejected.'
        messages.warning(request, errormessage)
        return redirect(reverse('submissions:pool'))
    if submission.editor_in_charge:
        errormessage = '<h3>Thank you for considering.</h3>'
        errormessage += (submission.editor_in_charge.get_title_display() + ' ' +
                         submission.editor_in_charge.user.last_name +
                         ' has already agreed to be Editor-in-charge of this Submission.')
        messages.warning(request, errormessage)
        return redirect(reverse('submissions:pool'))
    contributor = Contributor.objects.get(user=request.user)
    assignment = EditorialAssignment(submission=submission,
                                     to=contributor,
                                     accepted=True,
                                     date_created=timezone.now(),
                                     date_answered=timezone.now())
    deadline = timezone.now() + datetime.timedelta(days=28)  # for papers
    if submission.submitted_to_journal == 'SciPost Physics Lecture Notes':
        deadline += datetime.timedelta(days=28)
    submission.status = 'EICassigned'
    submission.editor_in_charge = contributor
    submission.open_for_reporting = True
    submission.reporting_deadline = deadline
    submission.open_for_commenting = True
    submission.latest_activity = timezone.now()
    assignment.save()
    submission.save()

    SubmissionUtils.load({'assignment': assignment})
    SubmissionUtils.deprecate_other_assignments()
    assign_perm('can_take_editorial_actions', contributor.user, submission)
    ed_admins = Group.objects.get(name='Editorial Administrators')
    assign_perm('can_take_editorial_actions', ed_admins, submission)
    SubmissionUtils.send_EIC_appointment_email()
    SubmissionUtils.send_author_prescreening_passed_email()

    messages.success(request, 'Thank you for becoming Editor-in-charge of this submission.')
    return redirect(reverse('submissions:editorial_page',
                            args=[submission.arxiv_identifier_w_vn_nr]))


@login_required
@permission_required('scipost.can_assign_submissions', raise_exception=True)
@transaction.atomic
def assignment_failed(request, arxiv_identifier_w_vn_nr):
    """
    No Editorial Fellow has accepted or volunteered to become Editor-in-charge.
    The submission is rejected.
    This method is called from pool.html by an Editorial Administrator.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if request.method == 'POST':
        form = ModifyPersonalMessageForm(request.POST)
        if form.is_valid():
            submission.status = 'assignment_failed'
            submission.latest_activity = timezone.now()
            submission.save()
            SubmissionUtils.load({'submission': submission,
                                  'personal_message': form.cleaned_data['personal_message']})
            SubmissionUtils.deprecate_all_assignments()
            SubmissionUtils.assignment_failed_email_authors()
            context = {'ack_header': ('Submission ' + submission.arxiv_identifier_w_vn_nr +
                                      ' has failed pre-screening and been rejected. '
                                      'Authors have been informed by email.'),
                       'followup_message': 'Return to the ',
                       'followup_link': reverse('submissions:pool'),
                       'followup_link_label': 'Submissions pool'}
            return render(request, 'scipost/acknowledgement.html', context)
    else:
        form = ModifyPersonalMessageForm()
    context = {'submission': submission,
               'form': form}
    return render(request, 'submissions/assignment_failed.html', context)


@login_required
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def assignments(request):
    """
    This page provides a Fellow with an explicit task list
    of editorial actions which should be undertaken.
    """
    assignments = EditorialAssignment.objects.filter(
        to=request.user.contributor).order_by('-date_created')
    assignments_to_consider = assignments.filter(accepted=None,
                                                 deprecated=False)
    current_assignments = assignments.filter(accepted=True,
                                             deprecated=False,
                                             completed=False)
    consider_assignment_form = ConsiderAssignmentForm()
    context = {
        'assignments_to_consider': assignments_to_consider,
        'consider_assignment_form': consider_assignment_form,
        'current_assignments': current_assignments,
    }
    return render(request, 'submissions/assignments.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def editorial_page(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    other_versions = (Submission.objects
                      .filter(arxiv_identifier_wo_vn_nr=submission.arxiv_identifier_wo_vn_nr)
                      .exclude(pk=submission.id))
    ref_invitations = RefereeInvitation.objects.filter(submission=submission)
    nr_reports_to_vet = (Report.objects
                         .filter(status=0, submission__editor_in_charge=request.user.contributor)
                         .count())
    communications = (EditorialCommunication.objects
                      .filter(submission=submission).order_by('timestamp'))
    try:
        recommendation = (EICRecommendation.objects.get_for_user_in_pool(request.user)
                          .get(submission=submission))
    except EICRecommendation.DoesNotExist:
        recommendation = None
    context = {'submission': submission,
               'other_versions': other_versions,
               'recommendation': recommendation,
               'set_deadline_form': SetRefereeingDeadlineForm(),
               'ref_invitations': ref_invitations,
               'nr_reports_to_vet': nr_reports_to_vet,
               'communications': communications}
    return render(request, 'submissions/editorial_page.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def select_referee(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    queryresults = ''
    if request.method == 'POST':
        ref_search_form = RefereeSelectForm(request.POST)
        if ref_search_form.is_valid():
            contributors_found = Contributor.objects.filter(
                user__last_name__icontains=ref_search_form.cleaned_data['last_name'])
            # Check for recent co-authorship (thus referee disqualification)
            if submission.metadata is not None:
                sub_auth_boolean_str = '((' + (submission
                                               .metadata['entries'][0]['authors'][0]['name']
                                               .split()[-1])
                for author in submission.metadata['entries'][0]['authors'][1:]:
                    sub_auth_boolean_str += '+OR+' + author['name'].split()[-1]
                sub_auth_boolean_str += ')+AND+'
                search_str = sub_auth_boolean_str + ref_search_form.cleaned_data['last_name'] + ')'
                queryurl = ('http://export.arxiv.org/api/query?search_query=au:%s'
                            % search_str + '&sortBy=submittedDate&sortOrder=descending'
                            '&max_results=5')
                arxivquery = feedparser.parse(queryurl)
                queryresults = arxivquery
    else:
        ref_search_form = RefereeSelectForm()
        contributors_found = None
    ref_recruit_form = RefereeRecruitmentForm()
    context = {'submission': submission, 'ref_search_form': ref_search_form,
               'contributors_found': contributors_found,
               'ref_recruit_form': ref_recruit_form,
               'queryresults': queryresults}
    return render(request, 'submissions/select_referee.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
@transaction.atomic
def recruit_referee(request, arxiv_identifier_w_vn_nr):
    """
    If the Editor-in-charge does not find the desired referee among Contributors
    (otherwise, the method send_refereeing_invitation below is used instead),
    he/she can invite somebody by providing name + contact details.
    This function emails a registration invitation to this person.
    The pending refereeing invitation is then recognized upon registration,
    using the invitation token.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if request.method == 'POST':
        ref_recruit_form = RefereeRecruitmentForm(request.POST)
        if ref_recruit_form.is_valid():
            # TODO check if email already taken
            ref_invitation = RefereeInvitation(
                submission=submission,
                title=ref_recruit_form.cleaned_data['title'],
                first_name=ref_recruit_form.cleaned_data['first_name'],
                last_name=ref_recruit_form.cleaned_data['last_name'],
                email_address=ref_recruit_form.cleaned_data['email_address'],
                date_invited=timezone.now(),
                invited_by=request.user.contributor)
            ref_invitation.save()
            # Create and send a registration invitation
            ref_inv_message_head = ('On behalf of the Editor-in-charge ' +
                                    submission.editor_in_charge.get_title_display() + ' ' +
                                    submission.editor_in_charge.user.last_name +
                                    ', we would like to invite you to referee a Submission to ' +
                                    submission.get_submitted_to_journal_display() +
                                    ', namely\n\n' + submission.title +
                                    '\nby ' + submission.author_list +
                                    '\n (see https://scipost.org/submission/'
                                    + submission.arxiv_identifier_w_vn_nr + ').')
            reg_invitation = RegistrationInvitation(
                title=ref_recruit_form.cleaned_data['title'],
                first_name=ref_recruit_form.cleaned_data['first_name'],
                last_name=ref_recruit_form.cleaned_data['last_name'],
                email=ref_recruit_form.cleaned_data['email_address'],
                invitation_type='R',
                invited_by=request.user.contributor,
                message_style='F',
                personal_message=ref_inv_message_head,
            )
            reg_invitation.save()
            Utils.load({'invitation': reg_invitation})
            Utils.send_registration_invitation_email()
            # Copy the key to the refereeing invitation:
            ref_invitation.invitation_key = reg_invitation.invitation_key
            ref_invitation.save()

    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
@transaction.atomic
def send_refereeing_invitation(request, arxiv_identifier_w_vn_nr, contributor_id):
    """
    This method is called by the EIC from the submission's editorial_page,
    in the case where the referee is an identified Contributor.
    For a referee who isn't a Contributor yet, the method recruit_referee above
    is called instead.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    contributor = get_object_or_404(Contributor, pk=contributor_id)
    if not contributor.is_currently_available():
        errormessage = ('This Contributor is marked as currently unavailable. '
                        'Please go back and select another referee.')
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    invitation = RefereeInvitation(submission=submission,
                                   referee=contributor,
                                   title=contributor.title,
                                   first_name=contributor.user.first_name,
                                   last_name=contributor.user.last_name,
                                   email_address=contributor.user.email,
                                   # the key is only used for inviting unregistered users
                                   invitation_key='notused',
                                   date_invited=timezone.now(),
                                   invited_by=request.user.contributor)
    invitation.save()
    # raise
    SubmissionUtils.load({'invitation': invitation})
    SubmissionUtils.send_refereeing_invitation_email()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def ref_invitation_reminder(request, arxiv_identifier_w_vn_nr, invitation_id):
    """
    This method is used by the Editor-in-charge from the editorial_page
    when a referee has been invited but hasn't answered yet.
    It can be used for registered as well as unregistered referees.
    """
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)
    invitation.nr_reminders += 1
    invitation.date_last_reminded = timezone.now()
    invitation.save()
    SubmissionUtils.load({'invitation': invitation})
    SubmissionUtils.send_ref_reminder_email()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitations(request):
    contributor = Contributor.objects.get(user=request.user)
    invitation = RefereeInvitation.objects.filter(referee=contributor, accepted=None).first()
    form = ConsiderRefereeInvitationForm()
    context = {'invitation_to_consider': invitation, 'form': form}
    return render(request, 'submissions/accept_or_decline_ref_invitations.html', context)


@login_required
@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitation_ack(request, invitation_id):
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)
    if request.method == 'POST':
        form = ConsiderRefereeInvitationForm(request.POST)
        if form.is_valid():
            invitation.date_responded = timezone.now()
            if form.cleaned_data['accept'] == 'True':
                invitation.accepted = True
            else:
                invitation.accepted = False
                invitation.refusal_reason = form.cleaned_data['refusal_reason']
            invitation.save()
            SubmissionUtils.load({'invitation': invitation})
            SubmissionUtils.email_referee_response_to_EIC()

    context = {'invitation': invitation}
    return render(request, 'submissions/accept_or_decline_ref_invitation_ack.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def cancel_ref_invitation(request, arxiv_identifier_w_vn_nr, invitation_id):
    """
    This method is used by the Editor-in-charge from the editorial_page
    to remove a referee for the list of invited ones.
    It can be used for registered as well as unregistered referees.
    """
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)
    invitation.cancelled = True
    invitation.save()
    SubmissionUtils.load({'invitation': invitation})
    SubmissionUtils.send_ref_cancellation_email()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def extend_refereeing_deadline(request, arxiv_identifier_w_vn_nr, days):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    submission.reporting_deadline += datetime.timedelta(days=int(days))
    submission.open_for_reporting = True
    submission.open_for_commenting = True
    submission.status = 'EICassigned'
    submission.latest_activity = timezone.now()
    submission.save()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def set_refereeing_deadline(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if request.method == 'POST':
        form = SetRefereeingDeadlineForm(request.POST)
        if form.is_valid():
            submission.reporting_deadline = form.cleaned_data['deadline']
            if form.cleaned_data['deadline'] > timezone.now().date():
                submission.open_for_reporting = True
                submission.open_for_commenting = True
            submission.status = 'EICassigned'
            submission.latest_activity = timezone.now()
            submission.save()
            context = {'ack_header': 'New reporting deadline set.',
                       'followup_message': 'Return to the ',
                       'followup_link': reverse('submissions:editorial_page',
                                                kwargs={'arxiv_identifier_w_vn_nr': submission.arxiv_identifier_w_vn_nr}),
                       'followup_link_label': 'Submission\'s Editorial Page'}
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The set reporting deadline form was improperly filled'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})

    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def close_refereeing_round(request, arxiv_identifier_w_vn_nr):
    """
    Called by the Editor-in-charge when a satisfactory number of
    reports have been gathered.
    Automatically emails the authors to ask them if they want to
    round off any replies to reports or comments before the
    editorial recommendation is formulated.
    """
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    submission.open_for_reporting = False
    submission.open_for_commenting = False
    if submission.status == 'EICassigned':  # only close if currently undergoing refereeing
        submission.status = 'review_closed'
    submission.reporting_deadline = timezone.now()
    submission.latest_activity = timezone.now()
    submission.save()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
def communication(request, arxiv_identifier_w_vn_nr, comtype, referee_id=None):
    """
    Communication between editor-in-charge, author or referee
    occurring during the submission refereeing.
    """
    submission = get_object_or_404(Submission, arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    errormessage = None
    if comtype not in dict(ED_COMM_CHOICES).keys():
        errormessage = 'Unknown type of cummunication.'
    # TODO: Verify that this is requested by an authorized contributor (eic, ref, author)
    elif (comtype in ['EtoA', 'EtoR', 'EtoS'] and
          not request.user.has_perm('can_take_editorial_actions', submission)):
        errormessage = 'Only the Editor-in-charge can perform this action.'
    elif (comtype in ['AtoE'] and
          not (request.user.contributor == submission.submitted_by)):
        errormessage = 'Only the corresponding author can perform this action.'
    elif (comtype in ['RtoE'] and
          not (RefereeInvitation.objects
               .filter(submission=submission, referee=request.user.contributor).exists())):
        errormessage = 'Only invited referees for this Submission can perform this action.'
    elif (comtype in ['StoE'] and
          not request.user.groups.filter(name='Editorial Administrators').exists()):
        errormessage = 'Only Editorial Administrators can perform this action.'
    if errormessage is not None:
        context = {'errormessage': errormessage, 'comtype': comtype}
        return render(request, 'submissions/communication.html', context)

    if request.method == 'POST':
        form = EditorialCommunicationForm(request.POST)
        if form.is_valid():
            communication = EditorialCommunication(submission=submission,
                                                   comtype=comtype,
                                                   timestamp=timezone.now(),
                                                   text=form.cleaned_data['text'])
            if referee_id is not None:
                referee = get_object_or_404(Contributor, pk=referee_id)
                communication.referee = referee
            communication.save()
            SubmissionUtils.load({'communication': communication})
            SubmissionUtils.send_communication_email()
            if comtype == 'EtoA' or comtype == 'EtoR' or comtype == 'EtoS':
                return redirect(reverse('submissions:editorial_page',
                                        kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))
            elif comtype == 'AtoE' or comtype == 'RtoE':
                return redirect(reverse('scipost:personal_page'))
            elif comtype == 'StoE':
                return redirect(reverse('submissions:pool'))
    else:
        form = EditorialCommunicationForm()
    context = {'submission': submission, 'comtype': comtype, 'referee_id': referee_id, 'form': form}
    return render(request, 'submissions/communication.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
@transaction.atomic
def eic_recommendation(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if submission.status not in ['EICassigned', 'review_closed']:
        errormessage = ('This submission\'s current status is: ' +
                        submission.get_status_display() + '. '
                        'An Editorial Recommendation is not required.')
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    if request.method == 'POST':
        form = EICRecommendationForm(request.POST)
        if form.is_valid():
            recommendation = EICRecommendation(
                submission=submission,
                date_submitted=timezone.now(),
                remarks_for_authors=form.cleaned_data['remarks_for_authors'],
                requested_changes=form.cleaned_data['requested_changes'],
                remarks_for_editorial_college=form.cleaned_data['remarks_for_editorial_college'],
                recommendation=form.cleaned_data['recommendation'],
                voting_deadline=timezone.now() + datetime.timedelta(days=7),
            )
            recommendation.save()
            # If recommendation is to accept or reject,
            # it is forwarded to the Editorial College for voting
            # If it is to carry out minor or major revisions,
            # it is returned to the Author who is asked to resubmit
            if (recommendation.recommendation == 1 or
                    recommendation.recommendation == 2 or
                    recommendation.recommendation == 3 or
                    recommendation.recommendation == -3):
                submission.status = 'voting_in_preparation'
            elif (recommendation.recommendation == -1 or
                  recommendation.recommendation == -2):
                submission.status = 'revision_requested'
                SubmissionUtils.load({'submission': submission,
                                      'recommendation': recommendation})
                SubmissionUtils.send_author_revision_requested_email()
            submission.open_for_reporting = False
            submission.save()

            # The EIC has fulfilled this editorial assignment.
            assignment = get_object_or_404(EditorialAssignment,
                                           submission=submission, to=request.user.contributor)
            assignment.completed = True
            assignment.save()
            return redirect(reverse('submissions:editorial_page',
                                    kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))
    else:
        form = EICRecommendationForm()
    context = {'submission': submission,
               'form': form}
    return render(request, 'submissions/eic_recommendation.html', context)


###########
# Reports
###########

@login_required
@permission_required('scipost.can_referee', raise_exception=True)
@transaction.atomic
def submit_report(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    # Check whether the user can submit a report:
    is_author = request.user.contributor in submission.authors.all()
    is_author_unchecked = (not is_author and not
                           (request.user.contributor in submission.authors_false_claims.all()) and
                           (request.user.last_name in submission.author_list))
    invited = RefereeInvitation.objects.filter(submission=submission,
                                               referee=request.user.contributor).exists()
    errormessage = None
    if not invited and timezone.now() > submission.reporting_deadline + datetime.timedelta(days=1):
        errormessage = ('The reporting deadline has passed. You cannot submit'
                        ' a Report anymore.')
    if is_author:
        errormessage = 'You are an author of this Submission and cannot submit a Report.'
    if is_author_unchecked:
        errormessage = ('The system flagged you as a potential author of this Submission. '
                        'Please go to your personal page under the Submissions tab to clarify this.')
    if errormessage:
        context = {'errormessage': errormessage}
        return render(request, 'submissions/submit_report_ack.html', context)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            if invited:
                invitation = RefereeInvitation.objects.get(submission=submission,
                                                           referee=request.user.contributor)
                invitation.fulfilled = True
                invitation.save()
            flagged = False
            if submission.referees_flagged is not None:
                if author.user.last_name in submission.referees_flagged:
                    flagged = True
            newreport = Report(
                submission=submission,
                author=author,
                invited=invited,
                flagged=flagged,
                qualification=form.cleaned_data['qualification'],
                strengths=form.cleaned_data['strengths'],
                weaknesses=form.cleaned_data['weaknesses'],
                report=form.cleaned_data['report'],
                requested_changes=form.cleaned_data['requested_changes'],
                validity=form.cleaned_data['validity'],
                significance=form.cleaned_data['significance'],
                originality=form.cleaned_data['originality'],
                clarity=form.cleaned_data['clarity'],
                formatting=form.cleaned_data['formatting'],
                grammar=form.cleaned_data['grammar'],
                recommendation=form.cleaned_data['recommendation'],
                remarks_for_editors=form.cleaned_data['remarks_for_editors'],
                anonymous=form.cleaned_data['anonymous'],
                date_submitted=timezone.now(),
            )
            newreport.save()
            author.nr_reports = Report.objects.filter(author=author).count()
            author.save()
            SubmissionUtils.load({'report': newreport})
            SubmissionUtils.email_EIC_report_delivered()
            request.session['arxiv_identifier_w_vn_nr'] = arxiv_identifier_w_vn_nr
            return HttpResponseRedirect(reverse('submissions:submit_report_ack'))

    else:
        form = ReportForm()
    context = {'submission': submission, 'form': form}
    return render(request, 'submissions/submit_report.html', context)


@login_required
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def vet_submitted_reports(request):
    contributor = Contributor.objects.get(user=request.user)
    report_to_vet = Report.objects.filter(status=0,
                                          submission__editor_in_charge=contributor).first()
    form = VetReportForm()
    context = {'contributor': contributor, 'report_to_vet': report_to_vet, 'form': form}
    return(render(request, 'submissions/vet_submitted_reports.html', context))


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
@transaction.atomic
def vet_submitted_report_ack(request, report_id):
    if request.method == 'POST':
        form = VetReportForm(request.POST)
        report = Report.objects.get(pk=report_id)
        if form.is_valid():
            report.vetted_by = request.user.contributor
            if form.cleaned_data['action_option'] == '1':
                # accept the report as is
                report.status = 1
                report.save()
                report.submission.latest_activity = timezone.now()
                report.submission.save()
            elif form.cleaned_data['action_option'] == '2':
                # the report is simply rejected
                report.status = int(form.cleaned_data['refusal_reason'])
                report.save()
            # email report author
            SubmissionUtils.load({'report': report,
                                  'email_response': form.cleaned_data['email_response_field']})
            SubmissionUtils.acknowledge_report_email()  # email report author, bcc EIC
            if report.status == 1:
                SubmissionUtils.send_author_report_received_email()
    context = {'ack_header': 'Submitted Report vetted.',
               'followup_message': 'Return to the ',
               'followup_link': reverse('submissions:editorial_page',
                                        kwargs={'arxiv_identifier_w_vn_nr': report.submission.arxiv_identifier_w_vn_nr}),
               'followup_link_label': 'Submission\'s Editorial Page'}
    return render(request, 'scipost/acknowledgement.html', context)


@permission_required('scipost.can_prepare_recommendations_for_voting', raise_exception=True)
@transaction.atomic
def prepare_for_voting(request, rec_id):
    recommendation = get_object_or_404((EICRecommendation.objects
                                        .get_for_user_in_pool(request.user)), id=rec_id)
    Fellows_with_expertise = Contributor.objects.filter(
        user__groups__name__in=['Editorial College'],
        expertises__contains=[recommendation.submission.subject_area])
    coauthorships = {}
    if request.method == 'POST':
        eligibility_form = VotingEligibilityForm(
            request.POST,
            discipline=recommendation.submission.discipline,
            subject_area=recommendation.submission.subject_area
        )
        if eligibility_form.is_valid():
            recommendation.eligible_to_vote = eligibility_form.cleaned_data['eligible_Fellows']
            recommendation.voted_for.add(recommendation.submission.editor_in_charge)
            recommendation.save()
            recommendation.submission.status = 'put_to_EC_voting'
            recommendation.submission.save()
            messages.success(request, 'We have registered your selection.')
            return redirect(reverse('submissions:editorial_page',
                                    args=[recommendation.submission.arxiv_identifier_w_vn_nr]))
    else:
        # Identify possible co-authorships in last 3 years, disqualifying Fellow from voting:
        if recommendation.submission.metadata is not None:
            for Fellow in Fellows_with_expertise:
                sub_auth_boolean_str = '((' + (recommendation.submission
                                               .metadata['entries'][0]['authors'][0]['name']
                                               .split()[-1])
                for author in recommendation.submission.metadata['entries'][0]['authors'][1:]:
                    sub_auth_boolean_str += '+OR+' + author['name'].split()[-1]
                    sub_auth_boolean_str += ')+AND+'
                    search_str = sub_auth_boolean_str + Fellow.user.last_name + ')'
                    queryurl = ('http://export.arxiv.org/api/query?search_query=au:%s'
                                % search_str + '&sortBy=submittedDate&sortOrder=descending'
                                '&max_results=5')
                    arxivquery = feedparser.parse(queryurl)
                    queryresults = arxivquery
                    if queryresults.entries:
                        coauthorships[Fellow.user.last_name] = queryresults

        eligibility_form = VotingEligibilityForm(
            discipline=recommendation.submission.discipline,
            subject_area=recommendation.submission.subject_area)

    context = {
        'recommendation': recommendation,
        'Fellows_with_expertise': Fellows_with_expertise,
        'coauthorships': coauthorships,
        'eligibility_form': eligibility_form,
    }
    return render(request, 'submissions/prepare_for_voting.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
@transaction.atomic
def vote_on_rec(request, rec_id):
    if request.method == 'POST':
        recommendation = get_object_or_404((EICRecommendation.objects
                                            .get_for_user_in_pool(request.user)), id=rec_id)
        form = RecommendationVoteForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['vote'] == 'agree':
                recommendation.voted_for.add(request.user.contributor)
                recommendation.voted_against.remove(request.user.contributor)
                recommendation.voted_abstain.remove(request.user.contributor)
            elif form.cleaned_data['vote'] == 'disagree':
                recommendation.voted_for.remove(request.user.contributor)
                recommendation.voted_against.add(request.user.contributor)
                recommendation.voted_abstain.remove(request.user.contributor)
            elif form.cleaned_data['vote'] == 'abstain':
                recommendation.voted_for.remove(request.user.contributor)
                recommendation.voted_against.remove(request.user.contributor)
                recommendation.voted_abstain.add(request.user.contributor)
            if form.cleaned_data['remark']:
                remark = Remark(contributor=request.user.contributor,
                                recommendation=recommendation,
                                date=timezone.now(),
                                remark=form.cleaned_data['remark'])
                remark.save()
            recommendation.save()
            return redirect(reverse('submissions:pool'))

    return redirect(reverse('submissions:pool'))


@permission_required('scipost.can_prepare_recommendations_for_voting', raise_exception=True)
def remind_Fellows_to_vote(request):
    """
    This method sends an email to all Fellow with pending voting duties.
    It must be called by and Editorial Administrator.
    """
    recommendations_undergoing_voting = (EICRecommendation.objects
                                         .get_for_user_in_pool(request.user)
                                         .filter(submission__status__in=['put_to_EC_voting']))
    Fellow_emails = []
    Fellow_names = []
    for rec in recommendations_undergoing_voting:
        for Fellow in rec.eligible_to_vote.all():
            if (Fellow not in rec.voted_for.all()
                and Fellow not in rec.voted_against.all()
                and Fellow not in rec.voted_abstain.all()
                and Fellow.user.email not in Fellow_emails):
                Fellow_emails.append(Fellow.user.email)
                Fellow_names.append(str(Fellow))
    SubmissionUtils.load({'Fellow_emails': Fellow_emails})
    SubmissionUtils.send_Fellows_voting_reminder_email()
    ack_message = 'Email reminders have been sent to: <ul>'
    for name in sorted(Fellow_names):
        ack_message += '<li>' + name + '</li>'
    ack_message += '</ul>'
    context = {'ack_message': Template(ack_message).render(Context({})),
               'followup_message': 'Return to the ',
               'followup_link': reverse('submissions:pool'),
               'followup_link_label': 'Submissions pool'}
    return render(request, 'scipost/acknowledgement.html', context)


@permission_required('scipost.can_fix_College_decision', raise_exception=True)
@transaction.atomic
def fix_College_decision(request, rec_id):
    """
    Terminates the voting on a Recommendation.
    Called by an Editorial Administrator.
    """
    recommendation = get_object_or_404((EICRecommendation.objects
                                        .get_for_user_in_pool(request.user)), pk=rec_id)
    if recommendation.recommendation == 1:
        # Publish as Tier I (top 10%)
        recommendation.submission.status = 'accepted'
    elif recommendation.recommendation == 2:
        # Publish as Tier II (top 50%)
        recommendation.submission.status = 'accepted'
    elif recommendation.recommendation == 3:
        # Publish as Tier III (meets criteria)
        recommendation.submission.status = 'accepted'
    elif recommendation.recommendation == -3:
        # Reject
        recommendation.submission.status = 'rejected'
        previous_submissions = Submission.objects.filter(
            arxiv_identifier_wo_vn_nr=recommendation.submission.arxiv_identifier_wo_vn_nr
        ).exclude(pk=recommendation.submission.id)
        for sub in previous_submissions:
            sub.status = 'resubmitted_rejected'
            sub.save()

    recommendation.submission.save()
    SubmissionUtils.load({'submission': recommendation.submission,
                          'recommendation': recommendation})
    SubmissionUtils.send_author_College_decision_email()
    ack_message = 'The Editorial College\'s decision has been fixed.'
    return render(request, 'scipost/acknowledgement.html',
                  context={'ack_message': ack_message})
