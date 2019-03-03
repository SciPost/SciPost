__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import mimetypes

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.utils import timezone

from guardian.decorators import permission_required

from mails.views import MailEditorSubview

from .constants import PROSPECTIVE_PARTNER_REQUESTED,\
    PROSPECTIVE_PARTNER_APPROACHED, PROSPECTIVE_PARTNER_ADDED,\
    PROSPECTIVE_PARTNER_EVENT_REQUESTED, PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT,\
    PROSPECTIVE_PARTNER_FOLLOWED_UP
from .models import Partner, ProspectivePartner, ProspectiveContact, ContactRequest,\
    ProspectivePartnerEvent, MembershipAgreement, Contact, PartnersAttachment
from .forms import ProspectivePartnerForm, ProspectiveContactForm,\
    PromoteToPartnerForm,\
    ProspectivePartnerEventForm, MembershipQueryForm,\
    PartnerForm, ContactForm, ContactFormset, ContactModelFormset,\
    NewContactForm, ActivationForm, PartnerEventForm,\
    MembershipAgreementForm, RequestContactForm, RequestContactFormSet,\
    ProcessRequestContactForm, PartnersAttachmentFormSet, PartnersAttachmentForm


def supporting_partners(request):
    current_agreements = MembershipAgreement.objects.now_active()
    context = {
        'current_agreements': current_agreements
    }
    if request.user.groups.filter(name='Editorial Administrators').exists():
        # Show Agreements to Administrators only!
        prospective_agreements = MembershipAgreement.objects.submitted().order_by('date_requested')
        context['prospective_partners'] = prospective_agreements
    return render(request, 'partners/supporting_partners.html', context)


@login_required
@permission_required('scipost.can_read_partner_page', return_403=True)
def dashboard(request):
    """Administration page for Partners and Prospective Partners.

    This page is meant as a personal page for Partners, where they will for example be able
    to read their personal data and agreements.
    """
    context = {}
    try:
        context['personal_agreements'] = (MembershipAgreement.objects.open_to_partner()
                                          .filter(partner__contact=request.user.partner_contact))
    except Contact.DoesNotExist:
        pass

    if request.user.has_perm('scipost.can_manage_SPB'):
        context['contact_requests_count'] = ContactRequest.objects.awaiting_processing().count()
        context['inactivate_contacts_count'] = Contact.objects.filter(user__is_active=False).count()
        context['partners'] = Partner.objects.all()
        context['prospective_partners'] = ProspectivePartner.objects.order_by(
            'country', 'institution_name')
        context['ppevent_form'] = ProspectivePartnerEventForm()
        context['agreements'] = MembershipAgreement.objects.order_by('date_requested')
    return render(request, 'partners/dashboard.html', context)


@transaction.atomic
def membership_request(request):
    query_form = MembershipQueryForm(request.POST or None)
    if query_form.is_valid():
        prospartner = ProspectivePartner(
            kind=query_form.cleaned_data['partner_kind'],
            institution_name=query_form.cleaned_data['institution_name'],
            country=query_form.cleaned_data['country'],
            date_received=timezone.now(),
            status=PROSPECTIVE_PARTNER_REQUESTED,
        )
        prospartner.save()
        contact = ProspectiveContact(
            prospartner=prospartner,
            title=query_form.cleaned_data['title'],
            first_name=query_form.cleaned_data['first_name'],
            last_name=query_form.cleaned_data['last_name'],
            email=query_form.cleaned_data['email'],
        )
        contact.save()
        prospartnerevent = ProspectivePartnerEvent(
            prospartner=prospartner,
            event=PROSPECTIVE_PARTNER_EVENT_REQUESTED)
        prospartnerevent.save()
        ack_message = ('Thank you for your SPB Membership query. '
                       'We will get back to you in the very near future '
                       'with further details.')
        context = {'ack_message': ack_message}
        return render(request, 'scipost/acknowledgement.html', context)
    context = {'query_form': query_form}
    return render(request, 'partners/membership_request.html', context)


@permission_required('scipost.can_manage_organizations', return_403=True)
@transaction.atomic
def promote_prospartner(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner.objects.not_yet_partner(),
                                    pk=prospartner_id)
    form = PromoteToPartnerForm(request.POST or None, instance=prospartner)
    contact_formset = ContactModelFormset(request.POST or None,
                                          queryset=prospartner.prospective_contacts.all())
    if form.is_valid() and contact_formset.is_valid():
        partner = form.promote_to_partner(request.user)
        contacts = contact_formset.promote_contacts(partner, request.user)
        messages.success(request, ('<h3>Upgraded Partner %s</h3>'
                                   '%i contacts have received a validation mail.') %
                                  (str(partner), len(contacts)))
        return redirect(reverse('partners:dashboard'))
    context = {'form': form, 'contact_formset': contact_formset}
    return render(request, 'partners/promote_prospartner.html', context)


###############
# Partner views
###############
@permission_required('scipost.can_view_own_partner_details', return_403=True)
def partner_view(request, partner_id):
    partner = get_object_or_404(Partner.objects.my_partners(request.user), id=partner_id)
    form = PartnerEventForm(request.POST or None)
    if form.is_valid():
        event = form.save(commit=False)
        event.partner = partner
        event.noted_by = request.user
        event.save()
        messages.success(request, 'Added a new event to Partner.')
        return redirect(partner.get_absolute_url())
    context = {
        'partner': partner,
        'form': form
    }
    return render(request, 'partners/partners_detail.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def partner_edit(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)

    # Start/fill forms
    form = PartnerForm(request.POST or None, instance=partner)
    ContactModelFormset = modelformset_factory(Contact, ContactForm, can_delete=True, extra=0,
                                               formset=ContactFormset)
    contact_formset = ContactModelFormset(request.POST or None, partner=partner,
                                          queryset=partner.contact_set.all())

    # Validate forms for POST request
    if form.is_valid() and contact_formset.is_valid():
        form.save()
        contact_formset.save()
        messages.success(request, 'Partner saved')
        return redirect(reverse('partners:partner_view', args=(partner.id,)))
    context = {
        'form': form,
        'contact_formset': contact_formset
    }
    return render(request, 'partners/partner_edit.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def partner_add_contact(request, partner_id):
    partner = get_object_or_404(Partner, id=partner_id)
    form = NewContactForm(request.POST or None, partner=partner)
    if form.is_valid():
        contact = form.save(current_user=request.user)
        messages.success(request, '<h3>Created contact: %s</h3>Email has been sent.'
                                  % str(contact))
        return redirect(reverse('partners:dashboard'))
    context = {
        'partner': partner,
        'form': form
    }
    return render(request, 'partners/partner_add_contact.html', context)


@permission_required('scipost.can_view_own_partner_details', return_403=True)
def partner_request_contact(request, partner_id):
    partner = get_object_or_404(Partner.objects.my_partners(request.user), id=partner_id)
    form = RequestContactForm(request.POST or None)
    if form.is_valid():
        contact_request = form.save(commit=False)
        contact_request.partner = partner
        contact_request.save()
        messages.success(request, ('<h3>Request sent</h3>'
                                   'We will process your request as soon as possible.'))
        return redirect(partner.get_absolute_url())
    context = {
        'partner': partner,
        'form': form
    }
    return render(request, 'partners/partner_request_contact.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def process_contact_requests(request):
    form = RequestContactForm(request.POST or None)

    RequestContactModelFormSet = modelformset_factory(ContactRequest, ProcessRequestContactForm,
                                                      formset=RequestContactFormSet, extra=0)
    formset = RequestContactModelFormSet(request.POST or None,
                                         queryset=ContactRequest.objects.awaiting_processing())
    if formset.is_valid():
        formset.process_requests(current_user=request.user)
        messages.success(request, 'Processing completed')
        return redirect(reverse('partners:process_contact_requests'))
    context = {
        'form': form,
        'formset': formset
    }
    return render(request, 'partners/process_contact_requests.html', context)



###########################
# Prospective Partner Views
###########################

@permission_required('scipost.can_manage_SPB', return_403=True)
def add_prospective_partner(request):
    form = ProspectivePartnerForm(request.POST or None)
    if form.is_valid():
        pp = form.save()
        messages.success(request, 'Prospective Partner successfully added')
        return redirect(reverse('partners:add_prospartner_contact',
                                kwargs={'prospartner_id': pp.id}))
    context = {'form': form}
    return render(request, 'partners/add_prospective_partner.html', context)


@permission_required('scipost.can_manage_SPB', return_403=True)
def add_prospartner_contact(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    form = ProspectiveContactForm(request.POST or None, initial={'prospartner': prospartner})
    if form.is_valid():
        form.save()
        messages.success(request, 'Contact successfully added to Prospective Partner')
        return redirect(reverse('partners:dashboard'))
    context = {'form': form, 'prospartner': prospartner}
    return render(request, 'partners/add_prospartner_contact.html', context)


@permission_required('scipost.can_email_prospartner_contact', return_403=True)
@transaction.atomic
def email_prospartner_contact(request, contact_id, mail=None):
    contact = get_object_or_404(ProspectiveContact, pk=contact_id)

    suffix = ''
    if mail == 'followup':
        code = 'partners_followup_mail'
        suffix = ' (followup)'
        new_status = PROSPECTIVE_PARTNER_FOLLOWED_UP
    else:
        code = 'partners_initial_mail'
        new_status = PROSPECTIVE_PARTNER_APPROACHED

    mail_request = MailEditorSubview(request, code, contact=contact)
    if mail_request.is_valid():
        comments = 'Email{suffix} sent to {name}.'.format(suffix=suffix, name=contact)
        prospartnerevent = ProspectivePartnerEvent(
            prospartner=contact.prospartner,
            event=PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user.contributor)
        prospartnerevent.save()
        if contact.prospartner.status in [PROSPECTIVE_PARTNER_REQUESTED,
                                          PROSPECTIVE_PARTNER_ADDED,
                                          PROSPECTIVE_PARTNER_APPROACHED]:
            contact.prospartner.status = new_status
            contact.prospartner.save()

        messages.success(request, 'Email successfully sent.')
        mail_request.send_mail()
        return redirect(reverse('partners:dashboard'))
    else:
        return mail_request.interrupt()


@permission_required('scipost.can_email_prospartner_contact', return_403=True)
@transaction.atomic
def email_prospartner_generic(request, prospartner_id, mail=None):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)

    suffix = ''

    if mail == 'followup':
        code = 'partners_followup_mail'
        suffix = ' (followup)'
        new_status = PROSPECTIVE_PARTNER_FOLLOWED_UP
    else:
        code = 'partners_initial_mail'
        new_status = PROSPECTIVE_PARTNER_APPROACHED

    mail_request = MailEditorSubview(request, mail_code=code, recipient_list=[])
    if mail_request.is_valid():
        comments = 'Email{suffix} sent to {name}.'.format(
            suffix=suffix, name=mail_request.recipients_string)
        prospartnerevent = ProspectivePartnerEvent(
            prospartner=prospartner,
            event=PROSPECTIVE_PARTNER_EVENT_EMAIL_SENT,
            comments=comments,
            noted_on=timezone.now(),
            noted_by=request.user.contributor)
        prospartnerevent.save()
        if prospartner.status in [PROSPECTIVE_PARTNER_REQUESTED,
                                  PROSPECTIVE_PARTNER_ADDED,
                                  PROSPECTIVE_PARTNER_APPROACHED]:
            prospartner.status = new_status
            prospartner.save()

        messages.success(request, 'Email successfully sent.')
        mail_request.send_mail()
        return redirect(reverse('partners:dashboard'))
    else:
        return mail_request.interrupt()


@permission_required('scipost.can_manage_SPB', return_403=True)
@transaction.atomic
def add_prospartner_event(request, prospartner_id):
    prospartner = get_object_or_404(ProspectivePartner, pk=prospartner_id)
    if request.method == 'POST':
        ppevent_form = ProspectivePartnerEventForm(request.POST)
        if ppevent_form.is_valid():
            ppevent = ppevent_form.save(commit=False)
            ppevent.prospartner = prospartner
            ppevent.noted_by = request.user.contributor
            ppevent.save()
            prospartner.update_status_from_event(ppevent.event)
            prospartner.save()
            return redirect(reverse('partners:dashboard'))
        else:
            errormessage = 'The form was invalidly filled.'
            return render(request, 'scipost/error.html', {'errormessage': errormessage})
    errormessage = 'This view can only be posted to.'
    return render(request, 'scipost/error.html', {'errormessage': errormessage})


############
# Agreements
############
@permission_required('scipost.can_manage_SPB', return_403=True)
def add_agreement(request):
    form = MembershipAgreementForm(request.POST or None, initial=request.GET)
    if request.POST and form.is_valid():
        agreement = form.save(request.user)
        messages.success(request, 'Membership Agreement created.')
        return redirect(agreement.get_absolute_url())
    context = {
        'form': form
    }
    return render(request, 'partners/agreements_add.html', context)


@permission_required('scipost.can_view_own_partner_details', return_403=True)
def agreement_details(request, agreement_id):
    agreement = get_object_or_404(MembershipAgreement, id=agreement_id)
    context = {}

    if request.user.has_perm('scipost.can_manage_SPB'):
        form = MembershipAgreementForm(request.POST or None, instance=agreement)
        PartnersAttachmentFormSet

        PartnersAttachmentFormset = modelformset_factory(PartnersAttachment,
                                                         PartnersAttachmentForm,
                                                         formset=PartnersAttachmentFormSet)
        attachment_formset = PartnersAttachmentFormset(request.POST or None, request.FILES or None,
                                                       queryset=agreement.attachments.all())

        context['form'] = form
        context['attachment_formset'] = attachment_formset
        if form.is_valid() and attachment_formset.is_valid():
            agreement = form.save(request.user)
            attachment_formset.save(agreement)
            messages.success(request, 'Membership Agreement updated.')
            return redirect(agreement.get_absolute_url())

    context['agreement'] = agreement
    return render(request, 'partners/agreements_details.html', context)


@permission_required('scipost.can_view_own_partner_details', return_403=True)
def agreement_attachments(request, agreement_id, attachment_id):
    attachment = get_object_or_404(PartnersAttachment.objects.my_attachments(request.user),
                                   agreement__id=agreement_id, id=attachment_id)

    content_type, encoding = mimetypes.guess_type(attachment.attachment.path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(attachment.attachment.read(), content_type=content_type)
    response["Content-Encoding"] = encoding
    response['Content-Disposition'] = ('filename=%s' % attachment.name)
    return response


#########
# Account
#########
def activate_account(request, activation_key):
    contact = get_object_or_404(Contact, user__is_active=False,
                                activation_key=activation_key,
                                user__email__icontains=request.GET.get('email', None))

    # TODO: Key Expires fallback
    form = ActivationForm(request.POST or None, instance=contact.user)
    if form.is_valid():
        form.activate_user()
        messages.success(request, '<h3>Thank you for registration</h3>')
        return redirect(reverse('partners:dashboard'))
    context = {
        'contact': contact,
        'form': form
    }
    return render(request, 'partners/activate_account.html', context)
