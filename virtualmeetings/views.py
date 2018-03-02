import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Context, Template
from django.utils import timezone

from .constants import motion_categories_dict
from .forms import FeedbackForm, NominationForm, MotionForm
from .models import VGM, Feedback, Nomination, Motion

from scipost.constants import SCIPOST_SUBJECT_AREAS
from scipost.forms import RemarkForm
from scipost.models import Contributor, Remark
from invitations.models import RegistrationInvitation


@login_required
@permission_required('scipost.can_attend_VGMs')
def VGMs(request):
    VGM_list = VGM.objects.all().order_by('start_date')
    context = {'VGM_list': VGM_list}
    return render(request, 'virtualmeetings/VGMs.html', context)


@login_required
@permission_required('scipost.can_attend_VGMs')
def VGM_detail(request, VGM_id):
    VGM_instance = get_object_or_404(VGM, id=VGM_id)
    VGM_information = Template(VGM_instance.information).render(Context({}))
    feedback_received = Feedback.objects.filter(VGM=VGM_instance).order_by('date')
    feedback_form = FeedbackForm()
    current_Fellows = Contributor.objects.filter(
        user__groups__name='Editorial College').order_by('user__last_name')

    pending_inv_Fellows = RegistrationInvitation.objects.for_fellows().no_response()
    declined_inv_Fellows = RegistrationInvitation.objects.for_fellows().declined()
    spec_list = SCIPOST_SUBJECT_AREAS  # subject_areas_dict
    nomination_form = NominationForm()
    nominations = Nomination.objects.filter(VGM=VGM_instance, accepted=None).order_by('last_name')
    motion_form = MotionForm()
    remark_form = RemarkForm()
    context = {
        'VGM': VGM_instance,
        'VGM_information': VGM_information,
        'feedback_received': feedback_received,
        'feedback_form': feedback_form,
        'current_Fellows': current_Fellows,
        'pending_inv_Fellows': pending_inv_Fellows,
        'declined_inv_Fellows': declined_inv_Fellows,
        'spec_list': spec_list,
        'nominations': nominations,
        'nomination_form': nomination_form,
        'motion_categories_dict': motion_categories_dict,
        'motion_form': motion_form,
        'remark_form': remark_form,
    }
    return render(request, 'virtualmeetings/VGM_detail.html', context)


@login_required
@permission_required('scipost.can_attend_VGMs')
def feedback(request, VGM_id=None):
    if request.method == 'POST':
        feedback_form = FeedbackForm(request.POST)
        if feedback_form.is_valid():
            feedback = Feedback(by=request.user.contributor,
                                date=timezone.now().date(),
                                feedback=feedback_form.cleaned_data['feedback'],)
            if VGM_id:
                VGM_instance = get_object_or_404(VGM, id=VGM_id)
                feedback.VGM = VGM_instance
            feedback.save()
            ack_message = 'Your feedback has been received.'
            context = {'ack_message': ack_message}
            if VGM_id:
                context['followup_message'] = 'Return to the '
                context['followup_link'] = reverse('virtualmeetings:VGM_detail',
                                                   kwargs={'VGM_id': VGM_id})
                context['followup_link_label'] = 'VGM page'
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was not filled properly.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def add_remark_on_feedback(request, VGM_id, feedback_id):
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    remark_form = RemarkForm(request.POST)
    if remark_form.is_valid():
        remark = Remark(contributor=request.user.contributor,
                        feedback=feedback,
                        remark=remark_form.cleaned_data['remark'])
        remark.save()
    else:
        messages.danger(request, 'The form was invalidly filled.')
    return redirect(feedback.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs')
def nominate_Fellow(request, VGM_id):
    VGM_instance = get_object_or_404(VGM, id=VGM_id)
    nomination_form = NominationForm(request.POST)

    if nomination_form.is_valid():
        nomination = nomination_form.save(commit=False)
        nomination.VGM = VGM_instance
        nomination.by = request.user.contributor
        nomination.voting_deadline = VGM_instance.end_date + datetime.timedelta(days=7)
        nomination.save()
        nomination.update_votes(request.user.contributor.id, 'A')
        messages.success(request, 'The nomination has been registered.')
    else:
        messages.warning(request, 'The form was not filled properly.')
    return redirect(VGM_instance.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def add_remark_on_nomination(request, VGM_id, nomination_id):
    # contributor = request.user.contributor
    nomination = get_object_or_404(Nomination, pk=nomination_id)
    remark_form = RemarkForm(request.POST)
    if remark_form.is_valid():
        remark = Remark(contributor=request.user.contributor,
                        nomination=nomination,
                        remark=remark_form.cleaned_data['remark'])
        remark.save()
    else:
        messages.danger(request, 'The form was invalidly filled.')
    return redirect(nomination.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def vote_on_nomination(request, nomination_id, vote):
    contributor = request.user.contributor
    nomination = get_object_or_404(Nomination, pk=nomination_id)
    if timezone.now() > nomination.voting_deadline:
        messages.warning(request, 'The voting deadline on this nomination has passed.')
    else:
        nomination.update_votes(contributor.id, vote)
        messages.success(request, 'You have successfully voted on nomination %i' % nomination.id)
    return redirect(nomination.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs')
def put_motion_forward(request, VGM_id):
    VGM_instance = get_object_or_404(VGM, id=VGM_id)
    if timezone.now().date() > VGM_instance.end_date:
        messages.warning(request, 'This VGM has ended. No new motions can be put forward.')
        return redirect(VGM_instance.get_absolute_url())

    motion_form = MotionForm(request.POST)
    if motion_form.is_valid():
        motion = Motion(
            category=motion_form.cleaned_data['category'],
            VGM=VGM_instance,
            background=motion_form.cleaned_data['background'],
            motion=motion_form.cleaned_data['motion'],
            put_forward_by=request.user.contributor,
            voting_deadline=VGM_instance.end_date + datetime.timedelta(days=7),
        )
        motion.save()
        motion.update_votes(request.user.contributor.id, 'A')
        messages.success(request, 'Your vote has been registered.')
    else:
        messages.danger(request, 'The form was not filled properly.')
    return redirect(motion.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def add_remark_on_motion(request, motion_id):
    motion = get_object_or_404(Motion, pk=motion_id)
    remark_form = RemarkForm(request.POST)
    if remark_form.is_valid():
        remark = Remark(contributor=request.user.contributor,
                        motion=motion,
                        remark=remark_form.cleaned_data['remark'])
        remark.save()
    else:
        messages.danger(request, 'The form was not filled properly.')
    return redirect(motion.get_absolute_url())


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def vote_on_motion(request, motion_id, vote):
    contributor = request.user.contributor
    motion = get_object_or_404(Motion, pk=motion_id)
    if timezone.now() > motion.voting_deadline:
        messages.warning(request, 'The voting deadline on this motion has passed.')
    else:
        motion.update_votes(contributor.id, vote)
        messages.success(request, 'You have successfully voted on motion %i' % motion.id)
    return redirect(motion.get_absolute_url())
