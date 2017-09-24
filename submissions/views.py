import datetime
import feedparser

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import transaction, IntegrityError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Template, Context
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm, get_objects_for_user

from .constants import SUBMISSION_STATUS_VOTING_DEPRECATED, STATUS_VETTED, STATUS_EIC_ASSIGNED,\
                       SUBMISSION_STATUS_PUBLICLY_INVISIBLE, SUBMISSION_STATUS, ED_COMM_CHOICES,\
                       STATUS_DRAFT, CYCLE_DIRECT_REC
from .models import Submission, EICRecommendation, EditorialAssignment,\
                    RefereeInvitation, Report, EditorialCommunication, SubmissionEvent
from .mixins import SubmissionAdminViewMixin
from .forms import SubmissionIdentifierForm, RequestSubmissionForm, SubmissionSearchForm,\
                   RecommendationVoteForm, ConsiderAssignmentForm, AssignSubmissionForm,\
                   SetRefereeingDeadlineForm, RefereeSelectForm, RefereeRecruitmentForm,\
                   ConsiderRefereeInvitationForm, EditorialCommunicationForm,\
                   EICRecommendationForm, ReportForm, VetReportForm, VotingEligibilityForm,\
                   SubmissionCycleChoiceForm, ReportPDFForm, SubmissionReportsForm,\
                   iThenticateReportForm
from .utils import SubmissionUtils

from mails.views import MailEditingSubView
from scipost.forms import ModifyPersonalMessageForm, RemarkForm
from scipost.models import Contributor, Remark, RegistrationInvitation
from scipost.utils import Utils
from comments.forms import CommentForm
from production.models import ProductionStream

import strings


###############
# SUBMISSIONS:
###############

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('scipost.can_submit_manuscript', raise_exception=True),
                  name='dispatch')
class RequestSubmission(CreateView):
    success_url = reverse_lazy('scipost:personal_page')
    form_class = RequestSubmissionForm
    template_name = 'submissions/new_submission.html'

    def get(self, request):
        return redirect('submissions:prefill_using_identifier')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['requested_by'] = self.request.user
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        submission = form.save()
        submission.add_general_event('The manuscript has been submitted to %s.'
                                     % submission.get_submitted_to_journal_display())

        text = ('<h3>Thank you for your Submission to SciPost</h3>'
                'Your Submission will soon be handled by an Editor.')
        messages.success(self.request, text)

        if form.submission_is_resubmission():
            # Send emails
            SubmissionUtils.load({'submission': submission}, self.request)
            SubmissionUtils.send_authors_resubmission_ack_email()
            SubmissionUtils.send_EIC_reappointment_email()
        else:
            # Send emails
            SubmissionUtils.load({'submission': submission})
            SubmissionUtils.send_authors_submission_ack_email()
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        for error_messages in form.errors.values():
            messages.warning(self.request, *error_messages)
        return super().form_invalid(form)


@login_required
@permission_required('scipost.can_submit_manuscript', raise_exception=True)
def prefill_using_arxiv_identifier(request):
    query_form = SubmissionIdentifierForm(request.POST or None, initial=request.GET or None)
    if query_form.is_valid():
        prefill_data = query_form.request_arxiv_preprint_form_prefill_data()
        form = RequestSubmissionForm(initial=prefill_data)

        # Submit message to user
        if query_form.submission_is_resubmission():
            resubmessage = ('There already exists a preprint with this arXiv identifier '
                            'but a different version number. \nYour Submission will be '
                            'handled as a resubmission.')
            messages.success(request, resubmessage, fail_silently=True)
        else:
            messages.success(request, strings.acknowledge_arxiv_query, fail_silently=True)

        context = {
            'form': form,
        }
        return render(request, 'submissions/new_submission.html', context)

    context = {
        'form': query_form,
    }
    return render(request, 'submissions/prefill_using_identifier.html', context)


class SubmissionListView(ListView):
    model = Submission
    template_name = 'submissions/submissions.html'
    form = SubmissionSearchForm
    submission_search_list = []
    paginate_by = 10

    def get_queryset(self):
        queryset = Submission.objects.public_newest()
        self.form = self.form(self.request.GET)
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
        elif self.form.is_valid() and self.form.has_changed():
            queryset = self.form.search_results()

        return queryset.order_by('-submission_date')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # Form into the context!
        context['form'] = self.form

        # To customize display in the template
        if 'to_journal' in self.kwargs:
            context['to_journal'] = self.kwargs['to_journal']
        if 'discipline' in self.kwargs:
            context['discipline'] = self.kwargs['discipline']
            context['nrweeksback'] = self.kwargs['nrweeksback']
            context['browse'] = True
        elif not self.form.is_valid() or not self.form.has_changed():
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
        is_author_unchecked = (not is_author and
                               request.user.contributor not in submission.authors_false_claims.all()
                               and request.user.last_name in submission.author_list)
        try:
            unfinished_report_for_user = (submission.reports.in_draft()
                                          .get(author=request.user.contributor))
        except Report.DoesNotExist:
            unfinished_report_for_user = None
    except AttributeError:
        is_author = False
        is_author_unchecked = False
        unfinished_report_for_user = None
    if (submission.status in SUBMISSION_STATUS_PUBLICLY_INVISIBLE
            and not request.user.groups.filter(name__in=['SciPost Administrators',
                                                         'Editorial Administrators',
                                                         'Editorial College']).exists()
            and not is_author):
        raise Http404

    form = CommentForm()

    invited_reports = submission.reports.accepted().filter(invited=True)
    contributed_reports = submission.reports.accepted().filter(invited=False)
    comments = (submission.comments.vetted()
                .filter(is_author_reply=False).order_by('-date_submitted'))
    author_replies = (submission.comments.vetted()
                      .filter(is_author_reply=True).order_by('-date_submitted'))

    recommendations = submission.eicrecommendations.all()

    context = {'submission': submission,
               'recommendations': recommendations,
               'comments': comments,
               'invited_reports': invited_reports,
               'contributed_reports': contributed_reports,
               'unfinished_report_for_user': unfinished_report_for_user,
               'author_replies': author_replies,
               'form': form,
               'is_author': is_author,
               'is_author_unchecked': is_author_unchecked}
    return render(request, 'submissions/submission_detail.html', context)


def report_detail_pdf(request, arxiv_identifier_w_vn_nr, report_nr):
    """
    Download the PDF of a Report if available.
    """
    report = get_object_or_404(Report.objects.accepted(),
                               submission__arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr,
                               pdf_report__isnull=False, report_nr=report_nr)
    response = HttpResponse(report.pdf_report.read(), content_type='application/pdf')
    filename = '%s_report-%i.pdf' % (report.submission.arxiv_identifier_w_vn_nr, report.report_nr)
    response['Content-Disposition'] = ('filename=' + filename)
    return response


def submission_refereeing_package_pdf(request, arxiv_identifier_w_vn_nr):
    """
    This view let's the user download all Report PDF's in a single merged PDF.
    The merging takes places every time its downloaded to make sure all available report PDF's
    are included and the EdColAdmin doesn't have to compile the package every time again.
    """
    submission = get_object_or_404(Submission.objects.public().exclude(pdf_refereeing_pack=''),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    response = HttpResponse(submission.pdf_refereeing_pack.read(), content_type='application/pdf')
    filename = '%s-refereeing-package.pdf' % submission.arxiv_identifier_w_vn_nr
    response['Content-Disposition'] = ('filename=' + filename)
    return response


@permission_required('scipost.can_manage_reports', raise_exception=True)
def reports_accepted_list(request):
    """
    This view lists all accepted Reports. This shows if Report needs a PDF update/compile
    in a convenient way.
    """
    reports = (Report.objects.accepted()
               .order_by('pdf_report', 'submission').prefetch_related('submission'))

    if request.GET.get('submission'):
        reports = reports.filter(submission__arxiv_identifier_w_vn_nr=request.GET.get('submission'))
    context = {
        'reports': reports
    }
    return render(request, 'submissions/reports_accepted_list.html', context)


@permission_required('scipost.can_manage_reports', raise_exception=True)
def report_pdf_compile(request, report_id):
    report = get_object_or_404(Report.objects.accepted(), id=report_id)
    form = ReportPDFForm(request.POST or None, request.FILES or None, instance=report)
    if form.is_valid():
        report = form.save()
        messages.success(request, 'Upload complete.')
        return redirect(reverse('submissions:reports_accepted_list'))
    context = {
        'report': report,
        'form': form
    }
    return render(request, 'submissions/reports_pdf_compile.html', context)


@permission_required('scipost.can_manage_reports', raise_exception=True)
def treated_submissions_list(request):
    """
    This view lists all accepted Reports. This shows if Report needs a PDF update/compile
    in a convenient way.
    """
    submissions = Submission.objects.treated().order_by('pdf_refereeing_pack', '-acceptance_date')
    context = {
        'submissions': submissions
    }
    return render(request, 'submissions/treated_submissions_list.html', context)


@permission_required('scipost.can_manage_reports', raise_exception=True)
def treated_submission_pdf_compile(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.treated(),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    form = SubmissionReportsForm(request.POST or None, request.FILES or None, instance=submission)
    if form.is_valid():
        form.save()
        messages.success(request, 'Upload complete.')
        return redirect(reverse('submissions:treated_submissions_list'))
    context = {
        'submission': submission,
        'form': form
    }
    return render(request, 'submissions/treated_submission_pdf_compile.html', context)


######################
# Editorial workflow #
######################

@login_required
@permission_required('scipost.can_view_pool', raise_exception=True)
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
                           .prefetch_related('referee_invitations', 'remarks', 'comments'))
    recommendations_undergoing_voting = (EICRecommendation.objects
                                         .get_for_user_in_pool(request.user)
                                         .filter(submission__status__in=['put_to_EC_voting']))
    recommendations_to_prepare_for_voting = (EICRecommendation.objects
                                             .get_for_user_in_pool(request.user)
                                             .filter(
                                                submission__status__in=['voting_in_preparation']))
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
            if not suggested_editor_in_charge.is_currently_available:
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

                # Add SubmissionEvents
                assignment.submission.add_general_event('The Editor-in-charge has been assigned.')
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

    # Add SubmissionEvents
    submission.add_general_event('The Editor-in-charge has been assigned.')

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
    submission = get_object_or_404(Submission.objects.filter_editorial_page(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)

    context = {
        'submission': submission,
        'set_deadline_form': SetRefereeingDeadlineForm(),
        'cycle_choice_form': SubmissionCycleChoiceForm(instance=submission),
    }
    return render(request, 'submissions/editorial_page.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def cycle_form_submit(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    form = SubmissionCycleChoiceForm(request.POST or None, instance=submission)
    if form.is_valid():
        submission = form.save()
        submission.cycle.update_status()
        submission.cycle.update_deadline()
        submission.cycle.reinvite_referees(form.cleaned_data['referees_reinvite'], request)
        messages.success(request, ('<h3>Your choice has been confirmed</h3>'
                                   'The new cycle will be <em>%s</em>'
                                   % submission.get_refereeing_cycle_display()))
        if submission.refereeing_cycle == CYCLE_DIRECT_REC:
            # Redirect to EIC Recommendation page immediately
            return redirect(reverse('submissions:eic_recommendation',
                            args=[submission.arxiv_identifier_w_vn_nr]))
    return redirect(reverse('submissions:editorial_page', args=[submission.arxiv_identifier_w_vn_nr]))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def select_referee(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.filter_editorial_page(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    context = {}
    queryresults = ''

    ref_search_form = RefereeSelectForm(request.POST or None)
    if ref_search_form.is_valid():
        contributors_found = Contributor.objects.filter(
            user__last_name__icontains=ref_search_form.cleaned_data['last_name'])
        context['contributors_found'] = contributors_found

        # Check for recent co-authorship (thus referee disqualification)
        try:
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
        except KeyError:
            pass
        context['ref_recruit_form'] = RefereeRecruitmentForm()

    context.update({
        'submission': submission,
        'ref_search_form': ref_search_form,
        'queryresults': queryresults
    })
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
    submission = get_object_or_404(Submission.objects.filter_editorial_page(request.user),
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
            submission.add_event_for_author('A referee has been invited.')
            submission.add_event_for_eic('%s has been recruited and invited as a referee.'
                                         % ref_recruit_form.cleaned_data['last_name'])
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
    if not contributor.is_currently_available:
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

    mail_request = MailEditingSubView(request, mail_code='submissions_referee_invite',
                                      invitation=invitation)
    if mail_request.is_valid():
        invitation.save()
        # SubmissionUtils.load({'invitation': invitation})
        # SubmissionUtils.send_refereeing_invitation_email()
        submission.add_event_for_author('A referee has been invited.')
        submission.add_event_for_eic('Referee %s has been invited.' % contributor.user.last_name)
        messages.success(request, 'Invitation sent')
        mail_request.send()
        return redirect(reverse('submissions:editorial_page',
                                kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))
    else:
        return mail_request.return_render()


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
    if invitation.referee is not None:
        SubmissionUtils.send_ref_reminder_email()
    else:
        SubmissionUtils.send_unreg_ref_reminder_email()
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitations(request):
    """
    RefereeInvitations need to be either accepted or declined by the invited user
    using this view. The decision will be taken one invitation at a time.
    """
    invitation = RefereeInvitation.objects.filter(referee__user=request.user,
                                                  accepted=None,
                                                  cancelled=False).first()
    if not invitation:
        messages.success(request, 'There are no Refereeing Invitations for you to consider.')
        return redirect(reverse('scipost:personal_page'))
    form = ConsiderRefereeInvitationForm()
    context = {'invitation_to_consider': invitation, 'form': form}
    return render(request, 'submissions/accept_or_decline_ref_invitations.html', context)


@login_required
@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitation_ack(request, invitation_id):
    invitation = get_object_or_404(RefereeInvitation, pk=invitation_id)
    form = ConsiderRefereeInvitationForm(request.POST or None)
    if form.is_valid():
        invitation.date_responded = timezone.now()
        if form.cleaned_data['accept'] == 'True':
            invitation.accepted = True
            decision_string = 'accepted'
        else:
            invitation.accepted = False
            decision_string = 'declined'
            invitation.refusal_reason = form.cleaned_data['refusal_reason']
        invitation.save()
        SubmissionUtils.load({'invitation': invitation}, request)
        SubmissionUtils.email_referee_response_to_EIC()
        SubmissionUtils.email_referee_in_response_to_decision()

        # Add SubmissionEvents
        invitation.submission.add_event_for_author('A referee has %s the refereeing invitation.'
                                                   % decision_string)
        invitation.submission.add_event_for_eic('Referee %s has %s the refereeing invitation.'
                                                % (invitation.referee.user.last_name,
                                                   decision_string))

    context = {'invitation': invitation}
    return render(request, 'submissions/accept_or_decline_ref_invitation_ack.html', context)


def decline_ref_invitation(request, invitation_key):
    invitation = get_object_or_404(RefereeInvitation, invitation_key=invitation_key,
                                   accepted__isnull=True)

    form = ConsiderRefereeInvitationForm(request.POST or None, initial={'accept': False})
    context = {'invitation': invitation, 'form': form}
    if form.is_valid():
        if form.cleaned_data['accept'] == 'True':
            # User filled in: Accept
            messages.warning(request, 'Please login and go to your personal page if you'
                                      ' want to accept the invitation.')
            return render(request, 'submissions/decline_ref_invitation.html', context)

        invitation.accepted = False
        invitation.refusal_reason = form.cleaned_data['refusal_reason']
        invitation.save()
        SubmissionUtils.load({'invitation': invitation}, request)
        SubmissionUtils.email_referee_response_to_EIC()

        # Add SubmissionEvents
        invitation.submission.add_event_for_author('A referee has declined the'
                                                   ' refereeing invitation.')
        invitation.submission.add_event_for_eic('Referee %s has declined the refereeing '
                                                'invitation.' % invitation.last_name)

        messages.success(request, 'Thank you for informing us that you will not provide a Report.')
        return redirect(reverse('scipost:index'))
    return render(request, 'submissions/decline_ref_invitation.html', context)


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

    # Add SubmissionEvents
    invitation.submission.add_event_for_author('A referee invitation has been cancelled.')
    invitation.submission.add_event_for_eic('Referee invitation for %s has been cancelled.'
                                            % invitation.last_name)

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

    submission.add_general_event('A new refereeing deadline is set.')
    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
def set_refereeing_deadline(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.get_pool(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)

    form = SetRefereeingDeadlineForm(request.POST or None)
    if form.is_valid():
        submission.reporting_deadline = form.cleaned_data['deadline']
        if form.cleaned_data['deadline'] > timezone.now().date():
            submission.open_for_reporting = True
            submission.open_for_commenting = True
        submission.status = 'EICassigned'
        submission.latest_activity = timezone.now()
        submission.save()
        submission.add_general_event('A new refereeing deadline is set.')
        context = {'ack_header': 'New reporting deadline set.',
                   'followup_message': 'Return to the ',
                   'followup_link': reverse('submissions:editorial_page',
                                            kwargs={'arxiv_identifier_w_vn_nr': submission.arxiv_identifier_w_vn_nr}),
                   'followup_link_label': 'Submission\'s Editorial Page'}
        return render(request, 'scipost/acknowledgement.html', context)
    else:
        messages.error(request, 'The deadline has not been set. Please try again.')

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
    submission.add_general_event('Refereeing round has been closed.')

    return redirect(reverse('submissions:editorial_page',
                            kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))


@permission_required('scipost.can_oversee_refereeing', raise_exception=True)
def refereeing_overview(request):
    submissions_under_refereeing = (Submission.objects.filter(status=STATUS_EIC_ASSIGNED)
                                    .order_by('submission_date'))
    context = {'submissions_under_refereeing': submissions_under_refereeing}
    return render(request, 'submissions/refereeing_overview.html', context)


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

    form = EditorialCommunicationForm(request.POST or None)
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
    context = {'submission': submission, 'comtype': comtype, 'referee_id': referee_id, 'form': form}
    return render(request, 'submissions/communication.html', context)


@login_required
@permission_required_or_403('can_take_editorial_actions',
                            (Submission, 'arxiv_identifier_w_vn_nr', 'arxiv_identifier_w_vn_nr'))
@transaction.atomic
def eic_recommendation(request, arxiv_identifier_w_vn_nr):
    submission = get_object_or_404(Submission.objects.filter_editorial_page(request.user),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    if submission.eic_recommendation_required():
        messages.warning(request, ('<h3>An Editorial Recommendation is not required</h3>'
                                   'This submission\'s current status is: <em>%s</em>'
                                   % submission.get_status_display()))
        return redirect(reverse('submissions:editorial_page',
                                args=[submission.arxiv_identifier_w_vn_nr]))

    # Find EditorialAssignment for user
    try:
        assignment = submission.editorial_assignments.get(submission=submission,
                                                          to=request.user.contributor)
    except EditorialAssignment.DoesNotExist:
        messages.warning(request, ('You cannot formulate an Editorial Recommendation,'
                                   ' because you are not assigned as editor-in-charge.'))
        return redirect(reverse('submissions:editorial_page',
                                args=[submission.arxiv_identifier_w_vn_nr]))

    form = EICRecommendationForm(request.POST or None)
    if form.is_valid():
        # Create new EICRecommendation
        recommendation = form.save(commit=False)
        recommendation.submission = submission
        recommendation.voting_deadline = timezone.now() + datetime.timedelta(days=7)
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

            # Add SubmissionEvent for EIC
            submission.add_event_for_eic('An Editorial Recommendation has been formulated: %s.'
                                         % recommendation.get_recommendation_display())

        elif (recommendation.recommendation == -1 or
              recommendation.recommendation == -2):
            submission.status = 'revision_requested'
            SubmissionUtils.load({'submission': submission,
                                  'recommendation': recommendation})
            SubmissionUtils.send_author_revision_requested_email()

            # Add SubmissionEvents
            submission.add_general_event('An Editorial Recommendation has been formulated: %s.'
                                         % recommendation.get_recommendation_display())
        submission.open_for_reporting = False
        submission.save()

        # The EIC has fulfilled this editorial assignment.
        assignment.completed = True
        assignment.save()
        messages.success(request, 'Your Editorial Recommendation has been succesfully submitted')
        return redirect(reverse('submissions:editorial_page',
                                kwargs={'arxiv_identifier_w_vn_nr': arxiv_identifier_w_vn_nr}))

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
    """
    A form to submit a report on a submission will be shown and processed here.

    Important checks to be aware of include an author check for the submission,
    has the reporting deadline not been reached yet and does there exist any invitation
    for the current user on this submission.
    """
    submission = get_object_or_404(Submission.objects.open_for_reporting(),
                                   arxiv_identifier_w_vn_nr=arxiv_identifier_w_vn_nr)
    # Check whether the user can submit a report:
    current_contributor = request.user.contributor
    is_author = current_contributor in submission.authors.all()
    is_author_unchecked = (not is_author and not
                           (current_contributor in submission.authors_false_claims.all()) and
                           (request.user.last_name in submission.author_list))
    invitation = submission.referee_invitations.filter(referee=current_contributor).first()

    errormessage = None
    if not invitation:
        if timezone.now() > submission.reporting_deadline + datetime.timedelta(days=1):
            errormessage = ('The reporting deadline has passed. You cannot submit'
                            ' a Report anymore.')
        elif not submission.open_for_reporting:
            errormessage = ('Reporting for this submission has closed. You cannot submit'
                            ' a Report anymore.')

        if errormessage:
            # Remove old drafts from the database
            reports_in_draft_to_remove = (submission.reports.in_draft()
                                          .filter(author=current_contributor))
            if reports_in_draft_to_remove:
                reports_in_draft_to_remove.delete()
    if is_author:
        errormessage = 'You are an author of this Submission and cannot submit a Report.'
    if is_author_unchecked:
        errormessage = ('The system flagged you as a potential author of this Submission. '
                        'Please go to your personal page under the Submissions tab'
                        ' to clarify this.')

    if errormessage:
        messages.warning(request, errormessage)
        return redirect(reverse('scipost:personal_page'))

    # Find and fill earlier version of report
    try:
        report_in_draft = submission.reports.in_draft().get(author=current_contributor)
    except Report.DoesNotExist:
        report_in_draft = Report(author=current_contributor, submission=submission)
    form = ReportForm(request.POST or None, instance=report_in_draft)

    # Check if data sent is valid
    if form.is_valid():
        newreport = form.save(submission)
        if newreport.status == STATUS_DRAFT:
            messages.success(request, ('Your Report has been saved. '
                                       'You may carry on working on it,'
                                       ' or leave the page and finish it later.'))
            context = {'submission': submission, 'form': form}
            return render(request, 'submissions/submit_report.html', context)

        # Send mails if report is submitted
        SubmissionUtils.load({'report': newreport}, request)
        SubmissionUtils.email_EIC_report_delivered()
        SubmissionUtils.email_referee_report_delivered()

        # Assign explicit permission to EIC to vet this report
        assign_perm('submissions.can_vet_submitted_reports', submission.editor_in_charge.user,
                    newreport)

        # Add SubmissionEvents for the EIC only, as it can also be rejected still
        submission.add_event_for_eic('%s has submitted a new Report.'
                                     % request.user.last_name)

        messages.success(request, 'Thank you for your Report')
        return redirect(reverse('scipost:personal_page'))

    context = {'submission': submission, 'form': form}
    return render(request, 'submissions/submit_report.html', context)


@login_required
@permission_required('submissions.can_vet_submitted_reports', raise_exception=True)
def vet_submitted_reports_list(request):
    """
    Reports with status `unvetted` will be shown (oldest first).
    """
    reports_to_vet = Report.objects.awaiting_vetting().order_by('date_submitted')
    context = {'reports_to_vet': reports_to_vet}
    return render(request, 'submissions/vet_submitted_reports_list.html', context)


@login_required
@transaction.atomic
def vet_submitted_report(request, report_id):
    """
    Report with status `unvetted` will be shown. A user may only vet reports of submissions
    he/she is EIC of or if he/she is SciPost Admin or Vetting Editor.

    After vetting an email is sent to the report author, bcc EIC. If report
    has not been refused, the submission author is also mailed.
    """
    # Method `get_objects_for_user` gets all Reports that are assigned to the user
    # or *all* Reports if user is SciPost Admin or Vetting Editor.
    report = get_object_or_404((get_objects_for_user(request.user,
                                                     'submissions.can_vet_submitted_reports')
                                .awaiting_vetting()), id=report_id)

    form = VetReportForm(request.POST or None, initial={'report': report})
    if form.is_valid():
        report = form.process_vetting(request.user.contributor)

        # email report author
        SubmissionUtils.load({'report': report,
                              'email_response': form.cleaned_data['email_response_field']})
        SubmissionUtils.acknowledge_report_email()  # email report author, bcc EIC

        # Add SubmissionEvent for the EIC
        report.submission.add_event_for_eic('The Report by %s is vetted.'
                                            % report.author.user.last_name)

        if report.status == STATUS_VETTED:
            SubmissionUtils.send_author_report_received_email()

            # Add SubmissionEvent to tell the author about the new report
            report.submission.add_event_for_author('A new Report has been submitted.')

        message = 'Submitted Report vetted for <a href="%s">%s</a>.' % (
                    report.submission.get_absolute_url(),
                    report.submission.arxiv_identifier_w_vn_nr)
        messages.success(request, message)

        if report.submission.editor_in_charge == request.user.contributor:
            # Redirect a EIC back to the Editorial Page!
            return redirect(reverse('submissions:editorial_page',
                                    args=(report.submission.arxiv_identifier_w_vn_nr,)))
        return redirect(reverse('submissions:vet_submitted_reports_list'))
    context = {'report_to_vet': report, 'form': form}
    return render(request, 'submissions/vet_submitted_report.html', context)


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

            # Add SubmissionEvents
            recommendation.submission.add_event_for_eic('The Editorial Recommendation has been '
                                                        'put forward to the College for voting.')

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
    recommendation = get_object_or_404((EICRecommendation.objects
                                        .get_for_user_in_pool(request.user)), id=rec_id)
    form = RecommendationVoteForm(request.POST or None)
    if form.is_valid():
        if form.cleaned_data['vote'] == 'agree':
            try:
                recommendation.voted_for.add(request.user.contributor)
            except IntegrityError:
                messages.warning(request, 'You have already voted for this Recommendation.')
                return redirect(reverse('submissions:pool'))
            recommendation.voted_against.remove(request.user.contributor)
            recommendation.voted_abstain.remove(request.user.contributor)
        elif form.cleaned_data['vote'] == 'disagree':
            recommendation.voted_for.remove(request.user.contributor)
            try:
                recommendation.voted_against.add(request.user.contributor)
            except IntegrityError:
                messages.warning(request, 'You have already voted for this Recommendation.')
                return redirect(reverse('submissions:pool'))
            recommendation.voted_abstain.remove(request.user.contributor)
        elif form.cleaned_data['vote'] == 'abstain':
            recommendation.voted_for.remove(request.user.contributor)
            recommendation.voted_against.remove(request.user.contributor)
            try:
                recommendation.voted_abstain.add(request.user.contributor)
            except IntegrityError:
                messages.warning(request, 'You have already voted for this Recommendation.')
                return redirect(reverse('submissions:pool'))
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

    TO FIX: If multiple recommendations are submitted; decisions may be overruled unexpectedly.
    """
    recommendation = get_object_or_404((EICRecommendation.objects
                                        .get_for_user_in_pool(request.user)), pk=rec_id)
    submission = recommendation.submission
    if recommendation.recommendation in [1, 2, 3]:
        # Publish as Tier I, II or III
        submission.status = 'accepted'
        submission.acceptance_date = datetime.date.today()

        # Create a ProductionStream object
        prodstream = ProductionStream(submission=submission)
        prodstream.save()

        # Add SubmissionEvent for authors
        # Do not write a new event for minor/major modification: already done at moment of
        # creation.
        submission.add_event_for_author('An Editorial Recommendation has been formulated: %s.'
                                        % recommendation.get_recommendation_display())
    elif recommendation.recommendation == -3:
        # Reject + update-reject other versions of submission
        submission.status = 'rejected'
        for sub in submission.other_versions:
            sub.status = 'resubmitted_rejected'
            sub.save()

        # Add SubmissionEvent for authors
        # Do not write a new event for minor/major modification: already done at moment of
        # creation.
        submission.add_event_for_author('An Editorial Recommendation has been formulated: %s.'
                                        % recommendation.get_recommendation_display())

    # Add SubmissionEvent for EIC
    submission.add_event_for_eic('The Editorial College\'s decision has been fixed: %s.'
                                 % recommendation.get_recommendation_display())

    submission.save()
    SubmissionUtils.load({'submission': submission, 'recommendation': recommendation})
    SubmissionUtils.send_author_College_decision_email()
    messages.success(request, 'The Editorial College\'s decision has been fixed.')
    return redirect(reverse('submissions:pool'))


class EICRecommendationView(SubmissionAdminViewMixin, DetailView):
    permission_required = 'scipost.can_fix_College_decision'
    template_name = 'submissions/admin/eic_recommendation_detail.html'
    editorial_page = True

    def get_context_data(self, *args, **kwargs):
        """ Get the EICRecommendation as a submission-related instance. """
        ctx = super().get_context_data(*args, **kwargs)
        ctx['object'] = get_object_or_404(ctx['submission'].eicrecommendations.all(),
                                          id=self.kwargs['rec_id'])
        return ctx


class EditorialSummaryView(SubmissionAdminViewMixin, ListView):
    """
    Show all submission currently active in a refereeing process.
    In addition show all EIC events of the last 24 hours.
    """
    permission_required = 'scipost.can_oversee_refereeing'
    template_name = 'submissions/admin/editorial_admin.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Pick submission from `submission_list` to include proper filters such as author filters.
        if self.kwargs.get('arxiv_identifier_w_vn_nr'):
            try:
                context['submission'] = context['submission_list'].get(
                    arxiv_identifier_w_vn_nr=self.kwargs['arxiv_identifier_w_vn_nr'])
            except Submission.DoesNotExist:
                context['submission'] = None

        if not context.get('submission'):
            context['latest_events'] = SubmissionEvent.objects.for_eic().last_hours()
        return context


class PlagiarismView(SubmissionAdminViewMixin, UpdateView):
    permission_required = 'scipost.can_do_plagiarism_checks'
    template_name = 'submissions/admin/plagiarism_report.html'
    editorial_page = True
    form_class = iThenticateReportForm

    def get_object(self):
        submission = super().get_object()
        return submission.plagiarism_report


class PlagiarismReportPDFView(SubmissionAdminViewMixin, SingleObjectMixin, RedirectView):
    permission_required = 'scipost.can_do_plagiarism_checks'
    editorial_page = True

    def get_redirect_url(self, *args, **kwargs):
        submission = self.get_object()
        if not submission.plagiarism_report:
            raise Http404
        url = submission.plagiarism_report.get_report_url()

        if not url:
            raise Http404
        return url
