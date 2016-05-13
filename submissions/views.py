import datetime
import feedparser
import re
import requests

from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg

from .models import *
from .forms import *

from comments.models import Comment
from scipost.models import Contributor, title_dict, RegistrationInvitation

from scipost.utils import Utils

from comments.forms import CommentForm



###############
# SUBMISSIONS:
###############

@permission_required('scipost.can_submit_manuscript', raise_exception=True)
def prefill_using_identifier(request):
    if request.method == "POST":
        identifierform = SubmissionIdentifierForm(request.POST)
        if identifierform.is_valid():
            identifierpattern = re.compile("^[0-9]{4,}.[0-9]{4,5}v[0-9]{1,2}$") # we allow 1 or 2 digits for version
            errormessage = ''
            if not identifierpattern.match(identifierform.cleaned_data['identifier']):
                errormessage = 'The identifier you entered is improperly formatted (did you forget the version number?).'
                form = SubmissionForm()
                return render(request, 'submissions/submit_manuscript.html',
                              {'identifierform': identifierform, 'form': form,
                               'errormessage': errormessage})
            # Otherwise we query arXiv for the information:
            try:
                queryurl = 'http://export.arxiv.org/api/query?id_list=%s' % identifierform.cleaned_data['identifier']
                arxivquery = feedparser.parse(queryurl)
                # If paper has been published, should comment on published version
                try:
                    arxiv_journal_ref = arxivquery['entries'][0]['arxiv_journal_ref']
                    errormessage = 'This paper has been published as ' + arxiv_journal_ref + '. You cannot submit it to SciPost anymore.'
                except: 
                    pass
                try:
                    arxiv_doi = arxivquery['entries'][0]['arxiv_doi']
                    errormessage = 'This paper has been published under DOI ' + arxiv_DOI + '. You cannot submit it to SciPost anymore.'
                except:
                    pass
                if errormessage != '':
                    form = SubmissionForm()
                    context = {'identifierform': identifierform, 'form': form,
                               'errormessage': errormessage}
                    return render(request, 'submissions/submit_manuscript.html', context)
                # otherwise prefill the form:
                metadata = arxivquery
                title = arxivquery['entries'][0]['title']
                authorlist = arxivquery['entries'][0]['authors'][0]['name']
                for author in arxivquery['entries'][0]['authors'][1:]:
                    authorlist += ', ' + author['name']
                arxiv_link = arxivquery['entries'][0]['id']
                abstract = arxivquery['entries'][0]['summary']
                form = SubmissionForm(
                    initial={'metadata': metadata,
                             'title': title, 'author_list': authorlist,
                             'arxiv_identifier': identifierform.cleaned_data['identifier'],
                             'arxiv_link': arxiv_link, 'abstract': abstract})
                context = {'identifierform': identifierform, 'form': form}
                return render(request, 'submissions/submit_manuscript.html', context)
            except:
                pass
        else:
            pass
    return redirect(reverse('submissions:submit_manuscript'))

                
@permission_required('scipost.can_submit_manuscript', raise_exception=True)
def submit_manuscript(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submitted_by = Contributor.objects.get(user=request.user)
            submission = Submission (
                submitted_by = submitted_by,
                submitted_to_journal = form.cleaned_data['submitted_to_journal'],
                discipline = form.cleaned_data['discipline'],
                domain = form.cleaned_data['domain'],
                specialization = form.cleaned_data['specialization'],
                status = 'unassigned', 
                title = form.cleaned_data['title'],
                author_list = form.cleaned_data['author_list'],
                abstract = form.cleaned_data['abstract'],
                arxiv_link = form.cleaned_data['arxiv_link'],
                submission_date = timezone.now(),
                referees_flagged = form.cleaned_data['referees_flagged'],
                )
            submission.save()
            return HttpResponseRedirect(reverse('submissions:submit_manuscript_ack'))
    else:
        identifierform = SubmissionIdentifierForm()
        form = SubmissionForm()
    return render(request, 'submissions/submit_manuscript.html',
                  {'identifierform': identifierform, 'form': form})


def submissions(request):
    if request.method == 'POST':
        form = SubmissionSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            submission_search_list = Submission.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author_list__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                status__gte=1,
                )
            submission_search_list.order_by('-pub_date')
        else:
            submission_search_list = [] 
           
    else:
        form = SubmissionSearchForm()
        submission_search_list = []

    submission_recent_list = Submission.objects.filter(
        status__gte=1, latest_activity__gte=timezone.now() + datetime.timedelta(days=-7)
        )
    submission_recent_list = Submission.objects.filter(status__gte=1)
    context = {'form': form, 'submission_search_list': submission_search_list, 
               'submission_recent_list': submission_recent_list }
    return render(request, 'submissions/submissions.html', context)


def browse(request, discipline, nrweeksback):
    if request.method == 'POST':
        form = SubmissionSearchForm(request.POST)
        if form.is_valid() and form.has_changed():
            submission_search_list = Submission.objects.filter(
                title__icontains=form.cleaned_data['title_keyword'],
                author_list__icontains=form.cleaned_data['author'],
                abstract__icontains=form.cleaned_data['abstract_keyword'],
                assigned=True,
                )
            submission_search_list.order_by('-submission_date')
        else:
            submission_search_list = []
        context = {'form': form, 'submission_search_list': submission_search_list }
        return HttpResponseRedirect(request, 'submissions/submissions.html', context)
    else:
        form = SubmissionSearchForm()
    submission_browse_list = Submission.objects.filter(
        assigned=True, discipline=discipline, 
        latest_activity__gte=timezone.now() + datetime.timedelta(weeks=-int(nrweeksback))
        )
    context = {'form': form, 'discipline': discipline, 'nrweeksback': nrweeksback, 
               'submission_browse_list': submission_browse_list }
    return render(request, 'submissions/submissions.html', context)


def submission_detail(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    comments = submission.comment_set.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            newcomment = Comment (
                submission = submission,
                author = author,
                is_rem = form.cleaned_data['is_rem'],
                is_que = form.cleaned_data['is_que'],
                is_ans = form.cleaned_data['is_ans'],
                is_obj = form.cleaned_data['is_obj'],
                is_rep = form.cleaned_data['is_rep'],
                is_val = form.cleaned_data['is_val'],
                is_lit = form.cleaned_data['is_lit'],
                is_sug = form.cleaned_data['is_sug'],
                comment_text = form.cleaned_data['comment_text'],
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                date_submitted = timezone.now(),
                )
            newcomment.save()
            author.nr_comments = Comment.objects.filter(author=author).count()
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('comments:comment_submission_ack'))
    else:
        form = CommentForm()

    reports = submission.report_set.all()
    try:
        author_replies = Comment.objects.filter(submission=submission, is_author_reply=True)
    except Comment.DoesNotExist:
        author_replies = ()
    context = {'submission': submission, 'comments': comments.filter(status__gte=1, is_author_reply=False).order_by('-date_submitted'), 
               'invited_reports': reports.filter(status__gte=1, invited=True), 
               'contributed_reports': reports.filter(status__gte=1, invited=False), 
               'author_replies': author_replies, 
               'form': form, }
    return render(request, 'submissions/submission_detail.html', context)


######################
# Editorial workflow #
######################

@permission_required('scipost.can_assign_submissions', raise_exception=True)
def assign_submissions(request):
    submission_to_assign = Submission.objects.filter(status='unassigned').first() # only handle one at at time
    if submission_to_assign is not None:
        form = AssignSubmissionForm(discipline=submission_to_assign.discipline)
#        form = AssignSubmissionForm(discipline=submission_to_assign.discipline, specialization=submission_to_assign.specialization) # reactivate later on
    else:
        form = AssignSubmissionForm(discipline='physics')        
    context = {'submission_to_assign': submission_to_assign, 'form': form }
    return render(request, 'submissions/assign_submissions.html', context)


@permission_required('scipost.can_assign_submissions', raise_exception=True)
def assign_submission_ack(request, submission_id):
    submission = Submission.objects.get(pk=submission_id)
    if request.method == 'POST':
        form = AssignSubmissionForm(request.POST, discipline=submission.discipline)
        if form.is_valid():
            editor_in_charge = form.cleaned_data['editor_in_charge']
            ed_assignment = EditorialAssignment(submission=submission,
                                                to=editor_in_charge,
                                                date_created=timezone.now())
            ed_assignment.save()
            submission.assigned = True
            submission.status = 'assigned'
            submission.latest_activity = timezone.now()
            submission.save()
    context = {}
    return render(request, 'submissions/assign_submission_ack.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def accept_or_decline_assignments(request):
    contributor = Contributor.objects.get(user=request.user)
    assignment = EditorialAssignment.objects.filter(to=contributor, accepted=None).first()
    form = ConsiderAssignmentForm()
    context = {'assignment_to_consider': assignment, 'form': form}
    return render(request, 'submissions/accept_or_decline_assignments.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def accept_or_decline_assignment_ack(request, assignment_id):
    contributor = Contributor.objects.get(user=request.user)
    assignment = get_object_or_404 (EditorialAssignment, pk=assignment_id)
    if request.method == 'POST':
        form = ConsiderAssignmentForm(request.POST)
        if form.is_valid():
            assignment.date_answered = timezone.now()
            deadline = timezone.now() + datetime.timedelta(days=28) # for papers
            if assignment.submission.submitted_to_journal == 'SciPost Physics Lecture Notes':
                deadline += datetime.timedelta(days=28)
            if form.cleaned_data['accept'] == 'True':
                assignment.accepted = True
                assignment.to = contributor
                assignment.submission.status = 'EICassigned'
                assignment.submission.editor_in_charge = contributor
                assignment.submission.reporting_deadline = deadline
                assignment.submission.save()
            else:
                assignment.accepted = False
                assignment.refusal_reason = form.cleaned_data['refusal_reason']
            assignment.save()

    context = {'assignment': assignment}
    return render(request, 'submissions/accept_or_decline_assignment_ack.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def editorial_page(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    ref_invitations = RefereeInvitation.objects.filter(submission=submission)

    communications = EditorialCommunication.objects.filter(submission=submission).order_by('timestamp')
    context = {'submission': submission, 'ref_invitations': ref_invitations, 'communications': communications}
    return render(request, 'submissions/editorial_page.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def select_referee(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    if request.method == 'POST':
        ref_search_form = RefereeSelectForm(request.POST)
        if ref_search_form.is_valid():
            contributors_found = Contributor.objects.filter(user__last_name__icontains=ref_search_form.cleaned_data['last_name'])
    else:
        ref_search_form = RefereeSelectForm()
        contributors_found = None
    ref_recruit_form = RefereeRecruitmentForm()
    context = {'submission': submission, 'ref_search_form': ref_search_form, 
               'contributors_found': contributors_found, 'ref_recruit_form': ref_recruit_form}
    return render(request, 'submissions/select_referee.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def recruit_referee(request, submission_id):
    """
    If the Editor-in-charge does not find the desired referee among Contributors,
    he/she can invite somebody by providing some personal details.
    This function sends a registration invitation to this person.
    The pending refereeing invitation is then recognized upon registration,
    using the invitation token.
    """
    submission = get_object_or_404(Submission, pk=submission_id)
    if request.method == 'POST':
        ref_recruit_form = RefereeRecruitmentForm(request.POST)
        if ref_recruit_form.is_valid():
            # TODO check if email already taken
            ref_invitation = RefereeInvitation(submission=submission, 
                                               title=ref_recruit_form.cleaned_data['title'],
                                               first_name=ref_recruit_form.cleaned_data['first_name'],
                                               last_name=ref_recruit_form.cleaned_data['last_name'],
                                               email_address=ref_recruit_form.cleaned_data['email_address'],
                                               date_invited=timezone.now(),
                                               invited_by = request.user.contributor)
            ref_invitation.save()

            # Create and send a registration invitation
            ref_inv_message_head = ('You have been invited to referee a Submission to SciPost Physics, namely\n' +
                                    submission.title[:50] + '\nby ' + submission.author_list + '.')
            reg_invitation = RegistrationInvitation (
                title = ref_recruit_form.cleaned_data['title'],
                first_name = ref_recruit_form.cleaned_data['first_name'],
                last_name = ref_recruit_form.cleaned_data['last_name'],
                email_address = ref_recruit_form.cleaned_data['email_address'],
                invitation_type = 'R',
                invited_by = request.user.contributor,
                message_style = 'F',
                personal_message = ref_inv_message_head,
            )
            reg_invitation.save()
            Utils.load({'invitation': reg_invitation})
            Utils.send_registration_invitation_email()
            # Copy the key to the refereeing invitation:
            ref_invitation.invitation_key = reg_invitation.invitation_key
            ref_invitation.save()

    return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))

            
@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def send_refereeing_invitation(request, submission_id, contributor_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    contributor = get_object_or_404(Contributor, pk=contributor_id)
    invitation = RefereeInvitation(submission=submission,
                                   referee=contributor, title=contributor.title, 
                                   first_name=contributor.user.first_name, last_name=contributor.user.last_name,
                                   email_address=contributor.user.email,
                                   date_invited=timezone.now(),
                                   invited_by = request.user.contributor)
    invitation.save()                                   
    return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))


@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitations(request):
    contributor = Contributor.objects.get(user=request.user)
    invitation = RefereeInvitation.objects.filter(referee=contributor, accepted=None).first()
    form = ConsiderRefereeInvitationForm()
    context = {'invitation_to_consider': invitation, 'form': form}
    return render(request, 'submissions/accept_or_decline_ref_invitations.html', context)


@permission_required('scipost.can_referee', raise_exception=True)
def accept_or_decline_ref_invitation_ack(request, invitation_id):
    contributor = Contributor.objects.get(user=request.user)
    invitation = get_object_or_404 (RefereeInvitation, pk=invitation_id)
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

    context = {'invitation': invitation}
    return render(request, 'submissions/accept_or_decline_ref_invitation_ack.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def extend_refereeing_deadline(request, submission_id, days):
    submission = get_object_or_404 (Submission, pk=submission_id)
    submission.reporting_deadline += datetime.timedelta(days=int(days))
    submission.save()
    return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))
    

@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def close_refereeing_round(request, submission_id):
    submission = get_object_or_404 (Submission, pk=submission_id)
    submission.open_for_reporting = False
    submission.status = 'review_closed'
    submission.reporting_deadline = timezone.now()
    submission.save()
    return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))


@login_required
def communication(request, submission_id, type, referee_id=None):
    """ 
    Communication between editor-in-charge, author or referee
    occurring during the submission refereeing.
    """
    submission = get_object_or_404 (Submission, pk=submission_id)
    # TODO: Verify that this is requested by an authorized contributor (eic, ref, author)
    if request.method == 'POST':
        form = EditorialCommunicationForm(request.POST)
        if form.is_valid():
            communication = EditorialCommunication(submission=submission,
                                                   type=type,
                                                   timestamp=timezone.now(),
                                                   text=form.cleaned_data['text'])
            if referee_id is not None:
                referee = get_object_or_404(Contributor, pk=referee_id)
                communication.referee = referee
            communication.save()
            if type == 'EtoA' or type == 'EtoR' or type == 'EtoS':
                return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))
            elif type == 'AtoE' or type == 'RtoE' or type == 'StoE':
                return redirect(request, reverse('scipost:personal_page'))
    else:
        form = EditorialCommunicationForm()
    context = {'submission': submission, 'type': type, 'form': form}
    return render(request, 'submissions/communication.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def eic_recommendation(request, submission_id):
    submission = get_object_or_404 (Submission, pk=submission_id)
    if request.method == 'POST':
        form = EICRecommendationForm(request.POST)
        if form.is_valid():
            recommendation = form.save()
            recommendation.submission = submission
            recommendation.date_submitted = timezone.now()
            recommendation.voting_deadline = timezone.now() + datetime.timedelta(days=7)
            recommendation.save()
            # If recommendation is to accept or reject, it is forwarded to the Editorial College for voting
            # If it is to carry out minor or major revisions, it is returned to the Author who is asked to resubmit
            return redirect(reverse('submissions:editorial_page', kwargs={'submission_id': submission_id}))
    else:
        form = EICRecommendationForm()
    context = {'submission': submission, 'form': form}
    return render(request, 'submissions/eic_recommendation.html', context)

        
###########
# Reports
###########

@permission_required('scipost.can_referee', raise_exception=True)
def submit_report(request, submission_id):
    submission = get_object_or_404 (Submission, pk=submission_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            author = Contributor.objects.get(user=request.user)
            invited = RefereeInvitation.objects.filter(submission=submission, referee=request.user.contributor).exists()
            if invited:
                invitation = RefereeInvitation.objects.get(submission=submission, referee=request.user.contributor)
                invitation.fulfilled = True
                invitation.save()
            flagged = False
            if author.user.last_name in submission.referees_flagged:
                flagged = True
            newreport = Report (
                submission = submission,
                author = author,
                invited = invited,
                flagged = flagged,
                qualification = form.cleaned_data['qualification'],
                strengths = form.cleaned_data['strengths'],
                weaknesses = form.cleaned_data['weaknesses'],
                report = form.cleaned_data['report'],
                requested_changes = form.cleaned_data['requested_changes'],
                validity = form.cleaned_data['validity'],
                significance = form.cleaned_data['significance'],
                originality = form.cleaned_data['originality'],
                clarity = form.cleaned_data['clarity'],
                formatting = form.cleaned_data['formatting'],
                grammar = form.cleaned_data['grammar'],
                recommendation = form.cleaned_data['recommendation'],
                remarks_for_editors = form.cleaned_data['remarks_for_editors'],
                anonymous = form.cleaned_data['anonymous'],
                date_submitted = timezone.now(),
                )
            newreport.save()
            author.nr_reports = Report.objects.filter(author=author).count()
            author.save()
            request.session['submission_id'] = submission_id
            return HttpResponseRedirect(reverse('submissions:submit_report_ack'))

    else:
        form = ReportForm()
    context = {'submission': submission, 'form': form }
    return render(request, 'submissions/submit_report.html', context)


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def vet_submitted_reports(request):
    contributor = Contributor.objects.get(user=request.user)
    report_to_vet = Report.objects.filter(status=0).first() # only handle one at a time
    form = VetReportForm()
    context = {'contributor': contributor, 'report_to_vet': report_to_vet, 'form': form }
    return(render(request, 'submissions/vet_submitted_reports.html', context))


@permission_required('scipost.can_take_charge_of_submissions', raise_exception=True)
def vet_submitted_report_ack(request, report_id):
    if request.method == 'POST':
        form = VetReportForm(request.POST)
        report = Report.objects.get(pk=report_id)
        if form.is_valid():
            if form.cleaned_data['action_option'] == '1':
                # accept the report as is
                report.status = 1
                report.save()
            elif form.cleaned_data['action_option'] == '2':
                # the report is simply rejected
                report.status = form.cleaned_data['refusal_reason']
                report.save()
                # email report author

    context = {}
    return render(request, 'submissions/vet_submitted_report_ack.html', context)

