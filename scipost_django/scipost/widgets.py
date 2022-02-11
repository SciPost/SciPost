__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import json

from django.forms.widgets import CheckboxSelectMultiple, Widget
from django.utils.safestring import mark_safe


class SelectButtonWidget(CheckboxSelectMultiple):
    template_name = "widgets/checkbox_as_btn.html"


class ReCaptcha(Widget):
    recaptcha_response_name = "g-recaptcha-response"
    recaptcha_challenge_name = "g-recaptcha-response"
    template_name = "widgets/nocaptcha.html"

    def __init__(self, public_key, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.public_key = public_key

    def value_from_datadict(self, data, files, name):
        return [
            data.get(self.recaptcha_challenge_name, None),
            data.get(self.recaptcha_response_name, None),
        ]

    def get_context(self, name, value, attrs):
        try:
            lang = attrs["lang"]
        except KeyError:
            # Get the generic language code
            lang = "en"

        try:
            context = super().get_context(name, value, attrs)
        except AttributeError:
            context = {"widget": {"attrs": self.build_attrs(attrs)}}
        context.update(
            {
                "public_key": self.public_key,
                "lang": lang,
                "options": mark_safe(json.dumps(self.attrs, indent=2)),
            }
        )
        return context
