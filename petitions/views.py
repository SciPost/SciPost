__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import random
import string

from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, render, redirect
from django.template import Context, Template

from .models import Petition, PetitionSignatory
from .forms import SignPetitionForm
from .utils import PetitionUtils


def petition(request, slug):
    petition = get_object_or_404(Petition, slug=slug)

    is_signed = False
    initial = {}
    if request.user.is_authenticated:
        is_signed = petition.petition_signatories.verified().filter(
            signatory=request.user.contributor).exists()
        affiliation = request.user.contributor.affiliations.first() or {}
        institition = affiliation.institution.name if affiliation else ''
        country = affiliation.institution.country if affiliation else ''
        initial = {
            'petition': petition,
            'title': request.user.contributor.title,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'country_of_employment': country,
            'affiliation': institition,
        }

    form = SignPetitionForm(request.POST or None, initial=initial, petition=petition,
                            current_user=request.user)
    if form.is_valid():
        signature = form.save(commit=False)
        signature.petition = petition
        message = ('<h3>Many thanks for signing!</h3>'
                   '<p>Please invite your colleagues to also sign.</p>')
        if request.user.is_authenticated:
            signature.signatory = request.user.contributor
            signature.verified = True
            PetitionUtils.load({'petition': petition})
            PetitionUtils.send_SPB_petition_signature_thanks(request.user.email)
        else:
            # Generate verification key and link
            salt = ""
            for i in range(5):
                salt = salt + random.choice(string.ascii_letters)
            salt = salt.encode('utf8')
            verificationsalt = form.cleaned_data['last_name']
            verificationsalt = verificationsalt.encode('utf8')
            verification_key = hashlib.sha1(salt+verificationsalt).hexdigest()
            signature.verification_key = verification_key
            message += '\n<p>You will receive an email with a verification link.</p>'
            email_text = ('Please click on the link below to confirm '
                          'your signature of the petition: \n'
                          'https://scipost.org/petitions/'
                          + petition.slug + '/verify_signature/' + verification_key + '.\n')
            email_text_html = (
                '<p>Please click on the link below to confirm '
                'your signature of the petition:</p>'
                '<p><a href="https://scipost.org/petitions/{{ slug }}/verify_signature'
                '/{{ key }}">confirm your signature</a></p>')
            html_template = Template(email_text_html)
            html_version = html_template.render(Context({'slug': petition.slug,
                                                         'key': verification_key}))
            emailmessage = EmailMultiAlternatives(
                'Petition signature verification',
                email_text,
                'SciPost petitions<petitions@scipost.org>',
                [form.cleaned_data['email']],
                bcc=['petitions@scipost.org'])
            emailmessage.attach_alternative(html_version, 'text/html')
            emailmessage.send()
        signature.save()
        messages.success(request, message)
        return redirect(petition.get_absolute_url())

    context = {
        'petition': petition,
        'is_signed': is_signed,
        'form': form,
    }
    return render(request, 'petitions/petition.html', context)


def verify_signature(request, slug, key):
    petition = get_object_or_404(Petition, slug=slug)
    try:
        signature = petition.petition_signatories.get(verification_key=key)
    except PetitionSignatory.DoesNotExist:
        messages.warning(request, ('Unknown signature key.'))
        return redirect(petition.get_absolute_url())

    if not signature.verified:
        # Slight reduction of db write-use
        signature.verified = True
        signature.save()
    messages.success(request, ('<h3>Many thanks for confirming your signature.</h3>'
                               '<p>Please invite your colleagues to also sign.</p>'))
    PetitionUtils.load({'petition': petition})
    PetitionUtils.send_SPB_petition_signature_thanks(signature.email)
    return redirect(petition.get_absolute_url())
