__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json
import requests

from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.utils.encoding import force_text

from .widgets import ReCaptcha


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.
    Uses Django 1.9's postgres ArrayField
    and a MultipleChoiceField for its formfield.
    """

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.MultipleChoiceField,
            'widget': forms.CheckboxSelectMultiple,
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        return super(ArrayField, self).formfield(**defaults)


class ReCaptchaField(forms.CharField):
    default_error_messages = {
        'captcha_invalid': 'Incorrect, please try again.',
        'captcha_error': 'Error verifying input, please try again.',
    }

    def __init__(self, use_ssl=None, attrs=None, *args, **kwargs):
        """
        ReCaptchaField can accepts attributes which is a dictionary of
        attributes to be passed to the ReCaptcha widget class. The widget will
        loop over any options added and create the RecaptchaOptions
        JavaScript variables as specified in
        https://developers.google.com/recaptcha/docs/display#render_param
        """
        if attrs is None:
            attrs = {}

        public_key = settings.RECAPTCHA_PUBLIC_KEY
        self.use_ssl = getattr(settings, 'RECAPTCHA_USE_SSL', True)
        self.widget = ReCaptcha(public_key=public_key, attrs=attrs)
        self.required = True
        self.verify_url = 'https://www.recaptcha.net/recaptcha/api/siteverify'
        super().__init__(*args, **kwargs)

    def clean(self, values):
        super().clean(values[0])
        recaptcha_response = force_text(values[0])

        if not self.required:
            return

        data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response
        }

        r = requests.post(
            self.verify_url,
            data=data,
            headers={
                'Content-type': 'application/x-www-form-urlencoded',
                'User-agent': 'reCAPTCHA Python'
            })
        try:
            r.raise_for_status()
            response = r.json()
            catpcha_success = response.get('success', False)
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout):
            raise ValidationError(
                self.error_messages['captcha_error']
            )

        if not catpcha_success:
            raise ValidationError(
                self.error_messages['captcha_invalid']
            )
        return values[0]


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
         return '{}, {} ({})'.format(obj.last_name, obj.first_name, obj.email)
