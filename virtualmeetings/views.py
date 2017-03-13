import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import Context, Template
from django.utils import timezone

from .constants import motion_categories_dict
from .forms import FeedbackForm, NominationForm, MotionForm
from .models import VGM, Feedback, Nomination, Motion

from scipost.forms import RegistrationInvitation, RemarkForm
from scipost.models import Contributor, Remark


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
    sent_inv_Fellows = RegistrationInvitation.objects.filter(
        invitation_type='F', responded=False)
    pending_inv_Fellows = sent_inv_Fellows.filter(declined=False).order_by('last_name')
    declined_inv_Fellows = sent_inv_Fellows.filter(declined=True).order_by('last_name')
    nomination_form = NominationForm()
    nominations = Nomination.objects.filter(accepted=None).order_by('last_name')
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
    # contributor = request.user.contributor
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    if request.method == 'POST':
        remark_form = RemarkForm(request.POST)
        if remark_form.is_valid():
            remark = Remark(contributor=request.user.contributor,
                            feedback=feedback,
                            date=timezone.now(),
                            remark=remark_form.cleaned_data['remark'])
            remark.save()
            return HttpResponseRedirect('/VGM/' + str(VGM_id) +
                                        '/#feedback_id' + str(feedback.id))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs')
def nominate_Fellow(request, VGM_id):
    VGM_instance = get_object_or_404(VGM, id=VGM_id)
    if request.method == 'POST':
        nomination_form = NominationForm(request.POST)
        if nomination_form.is_valid():
            nomination = Nomination(
                VGM=VGM_instance,
                by=request.user.contributor,
                date=timezone.now().date(),
                first_name=nomination_form.cleaned_data['first_name'],
                last_name=nomination_form.cleaned_data['last_name'],
                discipline=nomination_form.cleaned_data['discipline'],
                expertises=nomination_form.cleaned_data['expertises'],
                webpage=nomination_form.cleaned_data['webpage'],
                voting_deadline=VGM_instance.end_date + datetime.timedelta(days=7),
            )
            nomination.save()
            nomination.update_votes(request.user.contributor.id, 'A')
            ack_message = 'The nomination has been registered.'
            context = {'ack_message': ack_message,
                       'followup_message': 'Return to the ',
                       'followup_link': reverse('virtualmeetings:VGM_detail',
                                                kwargs={'VGM_id': VGM_id}),
                       'followup_link_label': 'VGM page'}
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was not filled properly.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def add_remark_on_nomination(request, VGM_id, nomination_id):
    # contributor = request.user.contributor
    nomination = get_object_or_404(Nomination, pk=nomination_id)
    if request.method == 'POST':
        remark_form = RemarkForm(request.POST)
        if remark_form.is_valid():
            remark = Remark(contributor=request.user.contributor,
                            nomination=nomination,
                            date=timezone.now(),
                            remark=remark_form.cleaned_data['remark'])
            remark.save()
            return HttpResponseRedirect('/VGM/' + str(VGM_id) +
                                        '/#nomination_id' + str(nomination.id))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def vote_on_nomination(request, nomination_id, vote):
    contributor = request.user.contributor
    nomination = get_object_or_404(Nomination, pk=nomination_id)
    if timezone.now() > nomination.voting_deadline:
        errormessage = 'The voting deadline on this nomination has passed.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    nomination.update_votes(contributor.id, vote)
    return HttpResponseRedirect('/VGM/' + str(nomination.VGM.id) +
                                '/#nomination_id' + str(nomination.id))


@login_required
@permission_required('scipost.can_attend_VGMs')
def put_motion_forward(request, VGM_id):
    VGM_instance = get_object_or_404(VGM, id=VGM_id)
    if timezone.now().date() > VGM_instance.end_date:
        errormessage = 'This VGM has ended. No new motions can be put forward.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    if request.method == 'POST':
        motion_form = MotionForm(request.POST)
        if motion_form.is_valid():
            motion = Motion(
                category=motion_form.cleaned_data['category'],
                VGM=VGM_instance,
                background=motion_form.cleaned_data['background'],
                motion=motion_form.cleaned_data['motion'],
                put_forward_by=request.user.contributor,
                date=timezone.now().date(),
                voting_deadline=VGM_instance.end_date + datetime.timedelta(days=7),
            )
            motion.save()
            motion.update_votes(request.user.contributor.id, 'A')
            ack_message = 'Your motion has been registered.'
            context = {'ack_message': ack_message,
                       'followup_message': 'Return to the ',
                       'followup_link': reverse('virtualmeetings:VGM_detail',
                                                kwargs={'VGM_id': VGM_id}),
                       'followup_link_label': 'VGM page'}
            return render(request, 'scipost/acknowledgement.html', context)
        else:
            errormessage = 'The form was not filled properly.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def add_remark_on_motion(request, motion_id):
    # contributor = request.user.contributor
    motion = get_object_or_404(Motion, pk=motion_id)
    if request.method == 'POST':
        remark_form = RemarkForm(request.POST)
        if remark_form.is_valid():
            remark = Remark(contributor=request.user.contributor,
                            motion=motion,
                            date=timezone.now(),
                            remark=remark_form.cleaned_data['remark'])
            remark.save()
            return HttpResponseRedirect('/VGM/' + str(motion.VGM.id) +
                                        '/#motion_id' + str(motion.id))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    else:
        errormessage = 'This view can only be posted to.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})


@login_required
@permission_required('scipost.can_attend_VGMs', raise_exception=True)
def vote_on_motion(request, motion_id, vote):
    contributor = request.user.contributor
    motion = get_object_or_404(Motion, pk=motion_id)
    if timezone.now() > motion.voting_deadline:
        errormessage = 'The voting deadline on this motion has passed.'
        return render(request, 'scipost/error.html', {'errormessage': errormessage})
    motion.update_votes(contributor.id, vote)
    return HttpResponseRedirect('/VGM/' + str(motion.VGM.id) +
                                '/#motion_id' + str(motion.id))
